import json
from unittest.mock import Mock

import httpx
import pytest

from droit_territorial import credentials
from droit_territorial.models import SourceError
from droit_territorial.runtime import Settings, Transport
from droit_territorial.server import build_server
from droit_territorial.service import Service
from droit_territorial.setup import probe_connection, setup_status


@pytest.fixture(autouse=True)
def clean_credentials(monkeypatch):
    for key in (
        "PISTE_CLIENT_ID",
        "PISTE_CLIENT_SECRET",
        "JUDILIBRE_KEY_ID",
        "PISTE_ENV",
        "JT_CREDENTIAL_STORE",
    ):
        monkeypatch.delenv(key, raising=False)


def test_default_never_opens_keyring(monkeypatch):
    read = Mock(side_effect=AssertionError("Must not open a keyring without opting in"))
    monkeypatch.setattr(credentials, "read_profile", read)
    settings = Settings.from_env()
    assert not settings.oauth_configured
    assert setup_status(settings)["legifrance"]["missing_variables"] == [
        "PISTE_CLIENT_ID",
        "PISTE_CLIENT_SECRET",
    ]
    read.assert_not_called()


def test_environment_profile_never_mixes_with_keyring(monkeypatch):
    monkeypatch.setenv("JT_CREDENTIAL_STORE", "keyring")
    monkeypatch.setenv("PISTE_CLIENT_ID", "env-client")
    read = Mock(return_value={})
    monkeypatch.setattr(credentials, "read_profile", read)
    settings = Settings.from_env()
    assert not settings.oauth_configured
    assert settings.client_id == "env-client" and not settings.client_secret
    assert all(call.args[0] != "piste" for call in read.call_args_list)
    assert setup_status(settings)["legifrance"]["missing_variables"] == ["PISTE_CLIENT_SECRET"]


def test_keyring_profiles_separate_environments(monkeypatch):
    monkeypatch.setenv("JT_CREDENTIAL_STORE", "keyring")
    monkeypatch.setenv("PISTE_ENV", "sandbox")
    backend = Mock()
    backend.get_password.side_effect = [
        json.dumps({"PISTE_CLIENT_ID": "secret-id", "PISTE_CLIENT_SECRET": "secret-value"}),
        None,
    ]
    monkeypatch.setattr(credentials, "secure_backend", lambda: backend)
    settings = Settings.from_env()
    assert settings.oauth_configured and settings.sandbox
    assert backend.get_password.call_args_list[0].args == (
        "juriste-territorial.piste.sandbox",
        "credentials",
    )
    report = json.dumps(setup_status(settings)) + repr(settings)
    assert "secret-id" not in report and "secret-value" not in report
    assert setup_status(settings)["legifrance"]["state"] == "configured_not_verified"


@pytest.mark.parametrize("raw", ['{"PISTE_CLIENT_ID":"id"}', '["secret"]', "malformed-secret"])
def test_invalid_profile_is_sanitized(monkeypatch, raw):
    backend = Mock()
    backend.get_password.return_value = raw
    monkeypatch.setattr(credentials, "secure_backend", lambda: backend)
    with pytest.raises(SourceError) as exc:
        credentials.read_profile("piste", "production")
    assert exc.value.problem.code == "credential_store_invalid"
    assert raw not in str(exc.value)


def test_locked_keyring_keeps_methodology_available(monkeypatch):
    monkeypatch.setenv("JT_CREDENTIAL_STORE", "keyring")
    backend = Mock()
    backend.get_password.side_effect = RuntimeError("sensitive-secret-in-backend-error")
    monkeypatch.setattr(credentials, "secure_backend", lambda: backend)
    settings = Settings.from_env()
    assert not settings.oauth_configured
    report = json.dumps(setup_status(settings))
    assert "credential_store_unavailable" in report
    assert "sensitive-secret" not in report


def test_configure_refuses_noninteractive_input(monkeypatch):
    monkeypatch.setattr(credentials.sys.stdin, "isatty", lambda: False)
    backend = Mock()
    monkeypatch.setattr(credentials, "secure_backend", lambda: backend)
    with pytest.raises(SourceError) as exc:
        credentials.configure("piste", "production")
    assert exc.value.problem.code == "interactive_terminal_required"
    backend.set_password.assert_not_called()


def test_configure_verifies_atomic_hidden_write(monkeypatch):
    monkeypatch.setattr(credentials.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(
        credentials.getpass, "getpass", Mock(side_effect=["private-id", "private-secret"])
    )
    backend = Mock()
    saved = {}
    backend.set_password.side_effect = lambda service, user, value: saved.update({"value": value})
    backend.get_password.side_effect = lambda *args: saved["value"]
    monkeypatch.setattr(credentials, "secure_backend", lambda: backend)
    result = credentials.configure("piste", "production")
    assert result["status"] == "stored_not_probed"
    backend.set_password.assert_called_once()
    assert json.loads(saved["value"])["PISTE_CLIENT_SECRET"] == "private-secret"
    assert "private-" not in json.dumps(result)


def test_configure_refuses_echo_fallback(monkeypatch):
    monkeypatch.setattr(credentials.sys.stdin, "isatty", lambda: True)

    def fallback(prompt):
        import warnings

        warnings.warn("cannot hide input", credentials.getpass.GetPassWarning, stacklevel=2)
        return "unsafe"

    monkeypatch.setattr(credentials.getpass, "getpass", fallback)
    backend = Mock()
    monkeypatch.setattr(credentials, "secure_backend", lambda: backend)
    with pytest.raises(SourceError) as exc:
        credentials.configure("piste", "production")
    assert exc.value.problem.code == "input_cancelled"
    backend.set_password.assert_not_called()


@pytest.mark.parametrize("failure", ["", KeyboardInterrupt()])
def test_interrupted_or_empty_configure_does_not_replace_profile(monkeypatch, failure):
    monkeypatch.setattr(credentials.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(credentials.getpass, "getpass", Mock(side_effect=["id", failure]))
    backend = Mock()
    monkeypatch.setattr(credentials, "secure_backend", lambda: backend)
    with pytest.raises(SourceError):
        credentials.configure("piste", "production")
    backend.set_password.assert_not_called()


async def test_missing_credentials_probe_does_not_contact_source():
    handler = Mock(side_effect=AssertionError("No network without credentials"))
    settings = Settings()
    service = Service(
        settings, Transport(settings, httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    )
    try:
        result = await build_server(service).call_tool("get_source_status", {"probe": True})
        assert result.is_error
        assert result.structured_content["connection_test"]["state"] == "not_run"
        handler.assert_not_called()
    finally:
        await service.close()


@pytest.mark.parametrize("provider", ["legifrance", "judilibre"])
async def test_probe_requires_real_search_and_fetch(service, provider):
    report = await probe_connection(service, provider)
    assert report["state"] == "verified_search_and_fetch"
    assert [x["operation"] for x in report["checks"]] == ["search", "fetch"]
    assert service.settings.client_secret not in json.dumps(report)


@pytest.mark.parametrize(
    "http_status,expected",
    [
        (401, "authorization_required"),
        (403, "authorization_required"),
        (429, "quota_exceeded"),
        (503, "source_unavailable"),
    ],
)
async def test_probe_errors_are_not_empty_results(http_status, expected):
    settings = Settings(client_id="private-id", client_secret="private-secret")

    def handler(request):
        return httpx.Response(http_status, text="private-secret")

    service = Service(
        settings, Transport(settings, httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    )
    try:
        report = await probe_connection(service, "legifrance")
        assert report["state"] == "failed" and expected in report["error_codes"]
        assert "private-secret" not in json.dumps(report)
    finally:
        await service.close()


async def test_successful_empty_search_is_not_full_validation(service, monkeypatch):
    async def empty(*args):
        return {"status": "ok", "results": [], "errors": []}

    monkeypatch.setattr(service, "search", empty)
    report = await probe_connection(service, "legifrance")
    assert report["state"] == "reachable_empty_result"
    assert len(report["checks"]) == 1


async def test_setup_guide_is_available_through_mcp(service):
    result = await build_server(service).call_tool("get_methodology", {"topic": "installation"})
    assert not result.is_error
    assert "PISTE_CLIENT_SECRET" in result.structured_content["text"]


@pytest.mark.parametrize("mode", ["plaintext", "auto"])
def test_unknown_credential_store_is_refused(monkeypatch, mode):
    monkeypatch.setenv("JT_CREDENTIAL_STORE", mode)
    with pytest.raises(SourceError) as exc:
        Settings.from_env()
    assert exc.value.problem.code == "invalid_configuration"
