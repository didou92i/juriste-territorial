"""One bounded HTTP/OAuth layer for official APIs; no caller-selected hosts."""

import asyncio
import json
import os
import time
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field

import httpx

from .credentials import load_credentials
from .models import SourceError

ALLOWED_HOSTS = frozenset(
    {
        "api.piste.gouv.fr",
        "sandbox-api.piste.gouv.fr",
        "oauth.piste.gouv.fr",
        "sandbox-oauth.piste.gouv.fr",
        "www.conseil-etat.fr",
        "www.legifrance.gouv.fr",
        "www.economie.gouv.fr",
        "www.cnil.fr",
        "www.cada.fr",
        "www.collectivites-locales.gouv.fr",
        "opendata.justice-administrative.fr",
        "www.conseil-constitutionnel.fr",
        "eur-lex.europa.eu",
        "curia.europa.eu",
        "www.numerique.gouv.fr",
    }
)


@dataclass
class Settings:
    client_id: str = field(default="", repr=False)
    client_secret: str = field(default="", repr=False)
    judilibre_key: str = field(default="", repr=False)
    sandbox: bool = False
    local_db: str = ""
    evidence_db: str = ""
    admin_db: str = ""
    principal: str = ""
    blocked_ids: frozenset[str] = frozenset()
    timeout: float = 20
    credential_issues: tuple[dict, ...] = ()

    @classmethod
    def from_env(cls):
        environment = os.getenv("PISTE_ENV", "production")
        if environment not in {"production", "sandbox"}:
            raise SourceError("invalid_configuration", "PISTE_ENV must be production or sandbox")
        credentials, issues = load_credentials(environment)
        return cls(
            client_id=credentials.get("PISTE_CLIENT_ID", ""),
            client_secret=credentials.get("PISTE_CLIENT_SECRET", ""),
            judilibre_key=credentials.get("JUDILIBRE_KEY_ID", ""),
            credential_issues=issues,
            sandbox=environment == "sandbox",
            local_db=os.getenv("JT_LOCAL_DB", ""),
            evidence_db=os.getenv("JT_EVIDENCE_DB", ""),
            admin_db=os.getenv("JT_ADMIN_DB", ""),
            principal=os.getenv("JT_PRINCIPAL", ""),
            blocked_ids=frozenset(
                x.strip() for x in os.getenv("JT_WITHDRAWN_IDS", "").split(",") if x.strip()
            ),
        )

    @property
    def oauth_configured(self):
        return bool(self.client_id and self.client_secret)

    @property
    def api_base(self):
        return "https://sandbox-api.piste.gouv.fr" if self.sandbox else "https://api.piste.gouv.fr"

    @property
    def token_url(self):
        host = "sandbox-oauth.piste.gouv.fr" if self.sandbox else "oauth.piste.gouv.fr"
        return f"https://{host}/api/oauth/token"


class Transport:
    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None):
        self.settings = settings
        self.client = client or httpx.AsyncClient(
            timeout=httpx.Timeout(settings.timeout, connect=5),
            follow_redirects=False,
            limits=httpx.Limits(max_connections=4, max_keepalive_connections=2),
            trust_env=False,
            headers={"User-Agent": "droit-territorial/0.4.0"},
        )
        self.semaphore = asyncio.Semaphore(3)
        self.auth_lock = asyncio.Lock()
        self._token = ""
        self._expires = 0.0
        self._measurement = ContextVar("jt_request_measurement", default=None)

    @contextmanager
    def measure(self):
        counters = {"network_requests": 0, "response_bytes": 0, "network_ms": 0}
        token = self._measurement.set(counters)
        try:
            yield counters
        finally:
            self._measurement.reset(token)

    async def close(self):
        await self.client.aclose()

    async def request(self, method, url, *, provider="official", max_bytes=8_000_000, **kwargs):
        target = httpx.URL(url)
        if (
            target.scheme != "https"
            or target.host not in ALLOWED_HOSTS
            or target.port not in (None, 443)
            or target.userinfo
        ):
            raise SourceError("disallowed_destination", "Destination not in the official allowlist")
        for attempt in range(2):
            counters = self._measurement.get()
            started = time.perf_counter()
            if counters is not None:
                counters["network_requests"] += 1
            try:
                async with self.semaphore, self.client.stream(method, url, **kwargs) as response:
                    status = response.status_code
                    if status in (401, 403):
                        raise SourceError(
                            "authorization_required",
                            f"Official source refused access ({status})",
                            provider,
                        )
                    if status == 404:
                        raise SourceError(
                            "reference_not_found",
                            "Official source did not find this reference",
                            provider,
                        )
                    if status == 429:
                        raise SourceError(
                            "quota_exceeded", "Provider quota reached; retry later", provider, True
                        )
                    if status >= 500 and attempt == 0:
                        await asyncio.sleep(0.15)
                        continue
                    if status >= 500:
                        raise SourceError(
                            "source_unavailable", "Official source unavailable", provider, True
                        )
                    if 300 <= status < 400:
                        raise SourceError(
                            "redirect_refused",
                            "Source redirected; destination must be reviewed",
                            provider,
                        )
                    if status >= 400:
                        raise SourceError(
                            "upstream_rejected",
                            f"Official source rejected request ({status})",
                            provider,
                        )
                    content = bytearray()
                    async for chunk in response.aiter_bytes():
                        content.extend(chunk)
                        if len(content) > max_bytes:
                            raise SourceError(
                                "document_too_large",
                                "Response exceeds the bounded reader",
                                provider,
                            )
                    if counters is not None:
                        counters["response_bytes"] += len(content)
                    return bytes(content)
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                if attempt == 0:
                    await asyncio.sleep(0.15)
                    continue
                raise SourceError(
                    "source_unavailable", "Network timeout or connection failure", provider, True
                ) from exc
            finally:
                if counters is not None:
                    counters["network_ms"] += round((time.perf_counter() - started) * 1000)
        raise SourceError("source_unavailable", "Source unavailable", provider, True)

    async def json(self, method, url, **kwargs):
        raw = await self.request(method, url, **kwargs)
        try:
            value = json.loads(raw)
            if not isinstance(value, dict):
                raise ValueError("Expected object")
            return value
        except (ValueError, UnicodeError) as exc:
            raise SourceError("invalid_response", "Source did not return a JSON object") from exc

    async def token(self, force=False):
        if not self.settings.oauth_configured:
            raise SourceError(
                "credentials_missing", "Configure PISTE_CLIENT_ID and PISTE_CLIENT_SECRET", "piste"
            )
        async with self.auth_lock:
            if not force and self._token and time.monotonic() < self._expires:
                return self._token
            data = await self.json(
                "POST",
                self.settings.token_url,
                provider="piste",
                data={
                    "grant_type": "client_credentials",
                    "scope": "openid",
                    "client_id": self.settings.client_id,
                    "client_secret": self.settings.client_secret,
                },
            )
            token = data.get("access_token")
            if not isinstance(token, str) or not token.strip():
                raise SourceError("invalid_response", "OAuth response has no access token", "piste")
            try:
                lifetime = min(float(data.get("expires_in", 0)), 86400)
            except (ValueError, TypeError):
                lifetime = 0
            self._token = token
            self._expires = time.monotonic() + max(0, lifetime - 60)
            return token

    async def api(self, provider: str, route: str, *, body=None, params=None):
        paths = {
            "legifrance": {
                "/search",
                "/consult/getArticle",
                "/consult/juri",
                "/consult/jorf",
                "/consult/legiPart",
            },
            "judilibre": {"/search", "/decision", "/taxonomy"},
        }
        if route not in paths.get(provider, set()):
            raise SourceError("unsupported_operation", "Operation is not exposed")
        if provider == "legifrance":
            url = self.settings.api_base + "/dila/legifrance/lf-engine-app" + route
        else:
            url = self.settings.api_base + "/cassation/judilibre/v1.0" + route
        use_key = provider == "judilibre" and bool(self.settings.judilibre_key)
        for attempt in range(2):
            headers = {"Accept": "application/json"}
            if use_key:
                headers["KeyId"] = self.settings.judilibre_key
            else:
                headers["Authorization"] = "Bearer " + await self.token(force=attempt > 0)
            try:
                return await self.json(
                    "POST" if provider == "legifrance" else "GET",
                    url,
                    provider=provider,
                    headers=headers,
                    json=body,
                    params=params,
                )
            except SourceError as exc:
                if exc.problem.code == "authorization_required" and attempt == 0 and not use_key:
                    continue
                raise
        raise SourceError("authorization_required", "Authorization refused", provider)
