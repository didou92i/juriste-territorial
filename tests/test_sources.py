import json
from datetime import date

import httpx
import pytest
from conftest import ARTICLE, BODY, JUDICIAL, article_payload

from droit_territorial.models import SourceError
from droit_territorial.runtime import Settings, Transport
from droit_territorial.sources import OfficialSources, normalise_legi, normalise_search, search_body


def test_unknown_environment_never_silently_uses_production(monkeypatch):
    monkeypatch.setenv("PISTE_ENV", "prod-typo")
    with pytest.raises(SourceError):
        Settings.from_env()


async def test_decision_date_is_not_publication_date(service):
    doc = await service.sources.judiciary_fetch(JUDICIAL)
    assert doc.decision_date == date(2026, 2, 1)
    assert doc.published_at is None


async def test_constitutional_consultation_does_not_guess_an_endpoint(service):
    with pytest.raises(SourceError) as exc:
        await service.sources.legi_fetch("CONSTEXT000000000001")
    assert exc.value.problem.code == "unsupported_operation"


def test_cetat_request_matches_official_faq_contract():
    body = search_body(
        "CESEDA", "CETAT", None, 2, date_start=date(2000, 1, 1), date_end=date(2005, 1, 1)
    )
    assert body["fond"] == "CETAT"
    assert body["recherche"]["filtres"] == [
        {"facette": "DATE_DECISION", "dates": {"start": "2000-01-01", "end": "2005-01-01"}}
    ]
    assert body["recherche"]["pageNumber"] == 2
    assert body["recherche"]["champs"][0]["criteres"][0]["typeRecherche"] in {
        "UN_DES_MOTS",
        "TOUS_LES_MOTS_DANS_UN_CHAMP",
    }


def test_code_date_is_not_publication_date():
    data = search_body("fpt", "CODE_DATE", date(2025, 1, 1), 1)
    assert data["recherche"]["filtres"] == [{"facette": "DATE_VERSION", "singleDate": "2025-01-01"}]
    with pytest.raises(SourceError, match="date"):
        search_body("fpt", "CODE_DATE", None, 1)


@pytest.mark.parametrize(
    "body",
    [
        {"article": {"num": "R1", "texte": BODY}},
        {"article": {"id": ARTICLE}},
        article_payload("LEGIARTI000000000002"),
    ],
)
def test_no_self_validation_of_requested_identity_or_missing_text(body):
    with pytest.raises(SourceError):
        normalise_legi(body, ARTICLE)


def test_malformed_search_not_empty_success():
    with pytest.raises(SourceError):
        normalise_search({"error": "unavailable"}, "CETAT")
    with pytest.raises(SourceError):
        normalise_search({"results": [{"id": "invented"}]}, "CETAT")


async def test_judilibre_parameters_follow_official_openapi(service):
    requests = []

    def handler(request):
        requests.append(request)
        if "oauth" in request.url.host:
            return httpx.Response(200, json={"access_token": "fake", "expires_in": 3600})
        if request.url.path.endswith("taxonomy"):
            return httpx.Response(200, json={"result": {"cc": "Cassation", "ca": "Appel"}})
        return httpx.Response(200, json={"results": [{"id": JUDICIAL}], "total": 1})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        source = OfficialSources(Transport(service.settings, client))
        await source.judiciary_search("test", 3, courts=["cc", "ca"], date_start=date(2020, 1, 1))
    request = requests[-1]
    assert request.url.params.get_list("jurisdiction") == ["cc", "ca"]
    assert request.url.params["page"] == "3"
    assert request.url.params["date_start"] == "2020-01-01"
    assert request.method == "GET"


async def test_unknown_court_refused(service):
    with pytest.raises(SourceError) as exc:
        await service.sources.judiciary_search("test", courts=["invented-court"])
    assert exc.value.problem.code == "unsupported_court"


@pytest.mark.parametrize(
    "status,code,count",
    [
        (429, "quota_exceeded", 1),
        (503, "source_unavailable", 2),
        (403, "authorization_required", 1),
        (404, "reference_not_found", 1),
        (302, "redirect_refused", 1),
    ],
)
async def test_network_errors_have_explicit_semantics(status, code, count):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(status, text="sensitive upstream error must not leak")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        transport = Transport(Settings(), client)
        with pytest.raises(SourceError) as exc:
            await transport.json("GET", "https://www.conseil-etat.fr/test")
    assert exc.value.problem.code == code
    assert "sensitive" not in str(exc.value)
    assert len(calls) == count


async def test_refresh_token_is_bounded():
    calls = []

    def handler(request):
        calls.append(request)
        if "oauth" in request.url.host:
            return httpx.Response(200, json={"access_token": "fake", "expires_in": 3600})
        return httpx.Response(401)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        transport = Transport(Settings(client_id="fake", client_secret="fake"), client)
        with pytest.raises(SourceError):
            await transport.api("legifrance", "/search", body={})
    assert len(calls) == 4


async def test_oauth_cache_and_missing_credentials():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(200, json={"access_token": "fake", "expires_in": 3600})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        transport = Transport(Settings(client_id="fake", client_secret="fake"), client)
        await transport.token()
        await transport.token()
        assert len(calls) == 1
        with pytest.raises(SourceError):
            await Transport(Settings(), client).token()


@pytest.mark.parametrize(
    "url",
    [
        "http://www.legifrance.gouv.fr/x",
        "https://localhost/x",
        "https://127.0.0.1/x",
        "https://www.legifrance.gouv.fr.evil.example/x",
        "https://user:secret@www.legifrance.gouv.fr/x",
        "https://www.legifrance.gouv.fr:444/x",
        "file:///etc/passwd",
    ],
)
async def test_disallowed_destinations_never_requested(url):
    def handler(_):
        pytest.fail("Network must not be used for a forbidden destination")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(SourceError) as exc:
            await Transport(Settings(), client).request("GET", url)
        assert exc.value.problem.code == "disallowed_destination"


async def test_oversized_and_invalid_response():
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, content=b"x" * 40))
    ) as client:
        transport = Transport(Settings(), client)
        with pytest.raises(SourceError) as exc:
            await transport.request("GET", "https://www.cnil.fr/test", max_bytes=20)
        assert exc.value.problem.code == "document_too_large"
        with pytest.raises(SourceError) as exc:
            await transport.json("GET", "https://www.cnil.fr/test")
        assert exc.value.problem.code == "invalid_response"


async def test_cetat_fetch_uses_jurisprudence_endpoint(service):
    requests = []
    identifier = "CETATEXT000000000003"

    def handler(request):
        requests.append(request)
        if "oauth" in request.url.host:
            return httpx.Response(200, json={"access_token": "fake"})
        return httpx.Response(200, json={"id": identifier, "texte": BODY})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        doc = await OfficialSources(Transport(service.settings, client)).legi_fetch(identifier)
    assert requests[-1].url.path.endswith("/consult/juri")
    assert json.loads(requests[-1].content) == {"textId": identifier}
    assert doc.legal_order == "administrative"
