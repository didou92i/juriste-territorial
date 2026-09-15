"""Official source adapters. Search discovery is deliberately separate from evidence."""

import re
from datetime import UTC, date, datetime
from hashlib import sha256

from bs4 import BeautifulSoup

from .models import Document, EndStatus, LegalOrder, SourceError, VersionInterval
from .runtime import ALLOWED_HOSTS, Transport

LEGI_ID = re.compile(r"(?:LEGIARTI|LEGITEXT|CETATEXT|JURITEXT|JORFTEXT|CONSTEXT)\d{12}")
JUDI_ID = re.compile(r"[a-f0-9]{24}")
FUNDS = {
    "codes": "CODE_DATE",
    "legislation": "LODA_DATE",
    "jorf": "JORF",
    "administrative_case_law": "CETAT",
    "constitutional_case_law": "CONSTIT",
}


def clean(value) -> str:
    if not isinstance(value, str):
        return ""
    return (
        BeautifulSoup(value, "html.parser").get_text(" ", strip=True)
        if "<" in value
        else value.strip()
    )


def source_date(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value / 1000, UTC).date()
        return date.fromisoformat(str(value)[:10])
    except (ValueError, TypeError, OverflowError, OSError):
        return None


def interval(start, end):
    first, last = source_date(start), source_date(end)
    if end is None:
        state = EndStatus.MISSING
    elif last is None:
        state = EndStatus.INVALID
    elif last.year == 2999:  # Légifrance's explicit open-end sentinel only.
        state, last = EndStatus.OPEN, None
    elif first and last <= first:
        state, last = EndStatus.INVALID, None
    else:
        state = EndStatus.KNOWN
    return VersionInterval(start=first, end=last, end_status=state)


def legi_url(identifier):
    if not LEGI_ID.fullmatch(identifier):
        raise SourceError("invalid_reference", "Unrecognized Légifrance identifier")
    route = {
        "LEGIARTI": "codes/article_lc",
        "LEGITEXT": "loda/id",
        "CETATEXT": "ceta/id",
        "JURITEXT": "juri/id",
        "JORFTEXT": "jorf/id",
        "CONSTEXT": "cons/id",
    }[identifier[:8]]
    return f"https://www.legifrance.gouv.fr/{route}/{identifier}"


def search_body(
    query,
    fund,
    as_of_date,
    page,
    size=10,
    *,
    article=None,
    code=None,
    date_start=None,
    date_end=None,
):
    filters = []
    if fund in {"CODE_DATE", "LODA_DATE"}:
        if as_of_date is None:
            raise SourceError("date_required", "A consolidation date is required")
        filters.append({"facette": "DATE_VERSION", "singleDate": as_of_date.isoformat()})
    if code:
        filters.append({"facette": "NOM_CODE", "valeurs": [code]})
    if date_start or date_end:
        dates = {k: v.isoformat() for k, v in {"start": date_start, "end": date_end}.items() if v}
        filters.append({"facette": "DATE_DECISION", "dates": dates})
    return {
        "fond": fund,
        "recherche": {
            "champs": [
                {
                    "typeChamp": "NUM_ARTICLE" if article else "ALL",
                    "operateur": "ET",
                    "criteres": [
                        {
                            "typeRecherche": "EXACTE" if article else "TOUS_LES_MOTS_DANS_UN_CHAMP",
                            "valeur": article or query,
                            "operateur": "ET",
                        }
                    ],
                }
            ],
            "filtres": filters,
            "pageNumber": page,
            "pageSize": size,
            "operateur": "ET",
            "sort": "PERTINENCE",
            "typePagination": "ARTICLE" if article else "DEFAUT",
        },
    }


def normalise_search(payload, fund):
    rows = payload.get("results")
    if not isinstance(rows, list):
        raise SourceError(
            "invalid_response", "Légifrance response lacks a results array", "legifrance"
        )
    found = {}
    for row in rows:
        if not isinstance(row, dict):
            raise SourceError("invalid_response", "Malformed search result", "legifrance")
        titles = row.get("titles") or []
        title = " — ".join(clean(t.get("title")) for t in titles if isinstance(t, dict))
        candidates = [row, *titles]
        for section in row.get("sections") or []:
            candidates.extend(section.get("extracts") or [])
        for entry in candidates:
            identifier = entry.get("id")
            if not isinstance(identifier, str) or not LEGI_ID.fullmatch(identifier):
                continue
            found[identifier] = {
                "provider": "legifrance",
                "canonical_id": identifier,
                "source_ref": "legifrance:" + identifier,
                "canonical_url": legi_url(identifier),
                "title": clean(entry.get("title")) or title or identifier,
                "code_title": title if fund == "CODE_DATE" else None,
                "article_number": clean(entry.get("num")),
                "fund": fund,
                "snippet": clean(entry.get("text") or entry.get("texte"))[:600],
                "evidence_status": "discovery_only",
                "content_trust": "untrusted_data",
            }
    if len(found) > 200:
        raise SourceError(
            "result_limit", "Too many references in a page; refine the query", "legifrance"
        )
    if rows and not found:
        raise SourceError(
            "unrecognized_results",
            "Results exist but their identifiers could not be parsed",
            "legifrance",
        )
    return list(found.values())


def _collect_text(node, depth=0):
    if depth > 30:
        raise SourceError("document_too_complex", "Document nesting exceeds the bounded reader")
    if not isinstance(node, dict):
        return ""
    parts = []
    for key in ("titre", "title", "num"):
        if node.get(key):
            parts.append(clean(node[key]))
    value = node.get("texte") or node.get("texteHtml") or node.get("text")
    if isinstance(value, str):
        parts.append(clean(value))
    for key in ("articles", "sections"):
        for child in node.get(key) or []:
            parts.append(_collect_text(child, depth + 1))
    return "\n\n".join(x for x in parts if x)


def normalise_legi(payload, requested):
    node = next(
        (payload[k] for k in ("article", "text") if isinstance(payload.get(k), dict)), payload
    )
    identifier = node.get("id") or node.get("cid")
    if identifier != requested or not LEGI_ID.fullmatch(str(identifier)):
        raise SourceError(
            "identity_unconfirmed",
            "Response did not independently confirm the requested identifier",
            "legifrance",
        )
    # An id/title without a substantive body must not count as a retrieved document.
    body = node.get("texte") or node.get("texteHtml") or node.get("text")
    if not body and not node.get("articles") and not node.get("sections"):
        raise SourceError(
            "content_missing", "Source returned metadata without the document text", "legifrance"
        )
    text = _collect_text(node)
    if not text:
        raise SourceError("content_missing", "No readable document text", "legifrance")
    prefix = identifier[:8]
    article = prefix == "LEGIARTI"
    order = (
        LegalOrder.ADMINISTRATIVE
        if prefix == "CETATEXT"
        else (LegalOrder.JUDICIAL if prefix == "JURITEXT" else LegalOrder.ANY)
    )
    return Document(
        provider="legifrance",
        canonical_id=identifier,
        canonical_url=legi_url(identifier),
        title=clean(node.get("titre") or node.get("title"))
        or f"Article {node.get('num', '')}".strip(),
        text=text,
        document_kind="article"
        if article
        else ("decision" if prefix in {"CETATEXT", "JURITEXT", "CONSTEXT"} else "text"),
        legal_order=order,
        court_or_issuer=clean(node.get("juridiction")) or None,
        source_authenticity="official",
        version=interval(node.get("dateDebut"), node.get("dateFin")),
        published_at=source_date(node.get("datePubli")),
        decision_date=source_date(node.get("dateDecision") or node.get("dateTexte"))
        if prefix in {"CETATEXT", "JURITEXT", "CONSTEXT"}
        else None,
        signed_at=source_date(node.get("dateTexte"))
        if prefix not in {"CETATEXT", "JURITEXT", "CONSTEXT"}
        else None,
        source_updated_at=str(node["lastUpdate"]) if node.get("lastUpdate") else None,
        source_complete=article or prefix in {"CETATEXT", "JURITEXT", "CONSTEXT"},
        truncation_reason=None
        if article or prefix in {"CETATEXT", "JURITEXT", "CONSTEXT"}
        else "Text tree completeness requires provider review",
        related_refs=[
            "legifrance:" + x
            for x in sorted(set(LEGI_ID.findall(str(node.get("liens", [])) + text)))
            if x != identifier
        ],
        warnings=[
            "Official retrieval does not establish material applicability or the effect of cross-references"
        ],
    )


class OfficialSources:
    def __init__(self, transport: Transport):
        self.transport = transport

    async def legi_search(self, query, kind, when, page=1, **kwargs):
        fund = FUNDS[kind]
        payload = await self.transport.api(
            "legifrance", "/search", body=search_body(query, fund, when, page, **kwargs)
        )
        results = normalise_search(payload, fund)
        total = payload.get("totalResultNumber")
        raw_size = len(payload["results"])
        has_more = page * 10 < total if isinstance(total, int) else raw_size >= 10
        return {
            "results": results,
            "has_more": has_more,
            "coverage": "Selected Légifrance fund; absence is not proof of exhaustiveness",
        }

    async def legi_fetch(self, identifier, when=None):
        if not LEGI_ID.fullmatch(identifier):
            raise SourceError("invalid_reference", "Unrecognized Légifrance reference")
        prefix = identifier[:8]
        if prefix == "LEGIARTI":
            route, body = "/consult/getArticle", {"id": identifier}
        elif prefix == "CONSTEXT":
            raise SourceError(
                "unsupported_operation",
                "Constitutional consultation needs a dedicated contract; use the official page reader",
                "legifrance",
            )
        elif prefix in {"CETATEXT", "JURITEXT"}:
            route, body = "/consult/juri", {"textId": identifier}
        elif prefix == "JORFTEXT":
            route, body = "/consult/jorf", {"textCid": identifier}
        else:
            if when is None:
                raise SourceError("date_required", "Date required for a consolidated text")
            route, body = "/consult/legiPart", {"textId": identifier, "date": when.isoformat()}
        return normalise_legi(await self.transport.api("legifrance", route, body=body), identifier)

    async def judiciary_search(self, query, page=0, *, courts=None, date_start=None, date_end=None):
        if courts:
            taxonomy = await self.transport.api(
                "judilibre", "/taxonomy", params={"id": "jurisdiction"}
            )
            values = taxonomy.get("result")
            if not isinstance(values, dict) or not set(courts) <= set(values):
                raise SourceError(
                    "unsupported_court",
                    "Court absent from the current JudiLibre taxonomy",
                    "judilibre",
                )
            if set(courts) & {"ce", "ta", "caa"}:
                raise SourceError(
                    "wrong_legal_order", "JudiLibre is a judicial corpus", "judilibre"
                )
        params = [
            ("query", query),
            ("page", page),
            ("page_size", 10),
            ("sort", "score"),
            ("order", "desc"),
        ]
        params += [("jurisdiction", court) for court in courts or []]
        params += [
            (key, value.isoformat())
            for key, value in {"date_start": date_start, "date_end": date_end}.items()
            if value
        ]
        payload = await self.transport.api("judilibre", "/search", params=params)
        rows = payload.get("results")
        if not isinstance(rows, list):
            raise SourceError(
                "invalid_response", "JudiLibre response lacks a results array", "judilibre"
            )
        results = []
        for row in rows:
            identifier = row.get("id")
            if not isinstance(identifier, str) or not JUDI_ID.fullmatch(identifier):
                raise SourceError(
                    "identity_unconfirmed",
                    "Search result has no valid source identifier",
                    "judilibre",
                )
            if identifier in self.transport.settings.blocked_ids:
                continue
            results.append(
                {
                    "provider": "judilibre",
                    "canonical_id": identifier,
                    "source_ref": "judilibre:" + identifier,
                    "canonical_url": f"https://www.courdecassation.fr/decision/{identifier}",
                    "title": f"{row.get('jurisdiction', '?')} — {row.get('decision_date', '?')} — {row.get('number', '?')}",
                    "snippet": clean(row.get("summary"))[:600],
                    "evidence_status": "discovery_only",
                    "legal_order": "judicial",
                    "content_trust": "untrusted_data",
                }
            )
        total = payload.get("total")
        more = (page + 1) * 10 < total if isinstance(total, int) else len(rows) >= 10
        return {
            "results": results,
            "has_more": more,
            "coverage": "JudiLibre judicial decisions; variable coverage by jurisdiction and date",
        }

    async def judiciary_fetch(self, identifier):
        if not JUDI_ID.fullmatch(identifier):
            raise SourceError("invalid_reference", "Unrecognized JudiLibre reference")
        if identifier in self.transport.settings.blocked_ids:
            raise SourceError("reference_unavailable", "Reference unavailable")
        node = await self.transport.api("judilibre", "/decision", params={"id": identifier})
        if node.get("id") != identifier:
            raise SourceError(
                "identity_unconfirmed",
                "Response did not confirm the requested decision",
                "judilibre",
            )
        text = clean(node.get("text"))
        if not text:
            raise SourceError("content_missing", "Decision body not returned", "judilibre")
        return Document(
            provider="judilibre",
            canonical_id=identifier,
            canonical_url=f"https://www.courdecassation.fr/decision/{identifier}",
            title=f"{node.get('jurisdiction', '?')} — {node.get('decision_date', '?')} — {node.get('number', '?')}",
            text=text,
            document_kind="decision",
            legal_order=LegalOrder.JUDICIAL,
            court_or_issuer=node.get("jurisdiction"),
            source_authenticity="official",
            decision_date=source_date(node.get("decision_date")),
            source_complete=True,
            source_updated_at=node.get("update_date"),
            warnings=[
                "Distinguish party submissions, reasons and operative part; no numeric authority score"
            ],
        )

    async def official_page(self, url):
        # No credentials, redirects, arbitrary protocols or chosen hosts.
        from urllib.parse import urlsplit

        parsed = urlsplit(url)
        if parsed.hostname not in ALLOWED_HOSTS or "piste.gouv.fr" in (parsed.hostname or ""):
            raise SourceError(
                "disallowed_destination", "Only registered official document sites are supported"
            )
        raw = await self.transport.request("GET", url, provider="official_web", max_bytes=3_000_000)
        soup = BeautifulSoup(raw, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "form"]):
            tag.decompose()
        main = soup.find("main") or soup.find("article") or soup.body
        text = main.get_text("\n", strip=True) if main else ""
        if len(text) < 100 or any(
            x in text[:4000].lower()
            for x in ("verify you are human", "enable javascript and cookies", "captcha")
        ):
            raise SourceError(
                "content_unavailable",
                "Official page did not yield a readable document",
                "official_web",
            )
        title = soup.title.get_text(strip=True) if soup.title else parsed.path
        return Document(
            provider="official_web",
            canonical_id=sha256(url.encode()).hexdigest(),
            canonical_url=url,
            title=title,
            text=text,
            document_kind="web_page",
            source_authenticity="official",
            source_complete=False,
            truncation_reason="Generic HTML extraction: completeness and legal version not established",
            related_refs=["legifrance:" + x for x in sorted(set(LEGI_ID.findall(str(main))))],
            warnings=["A government page may contain non-binding commentary; inspect its nature"],
        )
