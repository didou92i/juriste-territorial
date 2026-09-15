import json
from datetime import date

import httpx
import pytest
from conftest import ARTICLE, ARTICLE2, BODY, article_payload, search_payload

from droit_territorial.models import ClaimInput, SourceError
from droit_territorial.runtime import Settings, Transport
from droit_territorial.service import Service


async def test_withdrawn_legifrance_result_hidden(service):
    service.settings.blocked_ids = frozenset({ARTICLE})
    response = await service.search("test", ["codes"], as_of_date=date(2026, 9, 15))
    assert ARTICLE not in str(response["results"])


async def test_article_from_another_code_not_accepted(service):
    response = await service.legal_version("Un autre code", "R2122-8", date(2026, 9, 15))
    assert response["status"] == "version_unknown"


async def test_general_territorial_query_searches_texts_and_cetat():
    funds = []

    def handler(request):
        if "oauth" in request.url.host:
            return httpx.Response(200, json={"access_token": "fake", "expires_in": 3600})
        body = json.loads(request.content)
        funds.append(body["fond"])
        return httpx.Response(200, json={"results": [], "totalResultNumber": 0})

    settings = Settings(client_id="fake", client_secret="fake")
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        service = Service(settings, Transport(settings, client))
        answer = await service.search("temps de travail territorial", as_of_date=date(2026, 9, 15))
    assert set(funds) == {"CODE_DATE", "LODA_DATE", "JORF", "CETAT"}
    assert answer["status"] == "ok" and not answer["results"] and not answer["errors"]


async def test_failure_not_zero_results():
    service = Service(Settings())
    try:
        response = await service.search("temps de travail", as_of_date=date(2026, 9, 15))
        assert response["status"] == "error"
        assert len(response["errors"]) == 4
        assert all(e["code"] == "credentials_missing" for e in response["errors"])
    finally:
        await service.close()


async def test_partial_source_error_retains_success():
    def handler(request):
        if "oauth" in request.url.host:
            return httpx.Response(200, json={"access_token": "fake", "expires_in": 3600})
        fund = json.loads(request.content)["fond"]
        return (
            httpx.Response(429) if fund == "CETAT" else httpx.Response(200, json=search_payload())
        )

    settings = Settings(client_id="fake", client_secret="fake")
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        service = Service(settings, Transport(settings, client))
        response = await service.search(
            "test", source_types=["codes", "case_law"], as_of_date=date(2026, 4, 1)
        )
    assert response["status"] == "partial" and response["results"]
    assert response["errors"][0]["code"] == "quota_exceeded"


async def test_cursors_are_query_bound_and_do_not_skip_pages():
    pages = []

    def handler(request):
        if "oauth" in request.url.host:
            return httpx.Response(200, json={"access_token": "fake", "expires_in": 3600})
        page = json.loads(request.content)["recherche"]["pageNumber"]
        pages.append(page)
        return httpx.Response(200, json=search_payload(total=20))

    settings = Settings(client_id="fake", client_secret="fake")
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        service = Service(settings, Transport(settings, client))
        first = await service.search("q", ["codes"], as_of_date=date(2026, 4, 1))
        with pytest.raises(SourceError):
            await service.search(
                "different", ["codes"], as_of_date=date(2026, 4, 1), cursor=first["next_cursor"]
            )
        second = await service.search(
            "q", ["codes"], as_of_date=date(2026, 4, 1), cursor=first["next_cursor"]
        )
    assert pages == [1, 2]
    assert second["next_cursor"] is None


async def test_pagination_snapshot_preserves_the_whole_document(service):
    first = await service.fetch("legifrance:" + ARTICLE, date(2026, 9, 15), length=15)
    parts = [first["text"]]
    assert not first["response_complete"]
    while first["next_offset"]:
        first = await service.fetch(first["source_ref"], offset=first["next_offset"], length=15)
        parts.append(first["text"])
    assert BODY in "".join(parts)
    assert "Exception : B." in "".join(parts)
    with pytest.raises(SourceError):
        await service.fetch("legifrance:" + ARTICLE, offset=1)


async def test_quotation_and_invented_evidence(service):
    response = await service.fetch("legifrance:" + ARTICLE, date(2026, 9, 15))
    claim = ClaimInput(
        claim_id="c1",
        statement="Conclusion à analyser",
        evidence_id=response["evidence_id"],
        quote="Exception : B.",
    )
    check = service.check_evidence([claim])["claims"][0]
    assert check["quote_found"] and check["legal_validity"] == "not_assessed"
    assert check["semantic_support"] == "not_assessed"
    claim.quote = "Citation inventée"
    assert (
        "quote_not_in_retrieved_text"
        in service.check_evidence([claim])["claims"][0]["technical_issues"]
    )
    claim.evidence_id = "ev_invented"
    assert service.check_evidence([claim])["claims"][0]["status"] == "error"


async def test_source_issued_id_not_input_alone(service):
    with pytest.raises(SourceError):
        await service.fetch("evidence:" + ARTICLE)


async def test_withdrawal_invalidates_cached_public_evidence(service):
    response = await service.fetch("legifrance:" + ARTICLE)
    service.settings.blocked_ids = frozenset({ARTICLE})
    with pytest.raises(SourceError):
        await service.fetch(response["source_ref"])


async def test_dated_version_and_diff_fetch_real_versions():
    def handler(request):
        if "oauth" in request.url.host:
            return httpx.Response(200, json={"access_token": "fake", "expires_in": 3600})
        body = json.loads(request.content)
        if request.url.path.endswith("search"):
            when = body["recherche"]["filtres"][0]["singleDate"]
            return httpx.Response(
                200, json=search_payload(ARTICLE if when < "2026-04-01" else ARTICLE2)
            )
        identifier = body["id"]
        node = article_payload(
            identifier,
            start="2026-01-01" if identifier == ARTICLE else "2026-04-01",
            end="2026-04-01" if identifier == ARTICLE else "2999-01-01",
            body="Ancienne condition fictive"
            if identifier == ARTICLE
            else "Nouvelle condition fictive",
        )
        return httpx.Response(200, json=node)

    settings = Settings(client_id="fake", client_secret="fake")
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        service = Service(settings, Transport(settings, client))
        comparison = await service.compare_versions(
            "Code de test", "R. 2122-8", date(2026, 3, 31), date(2026, 4, 1)
        )
    assert comparison["status"] == "ok" and comparison["changed"]
    assert "-Ancienne" in comparison["diff"] and "+Nouvelle" in comparison["diff"]
    assert comparison["legal_effect"] == "not_assessed"


async def test_expired_evidence_cannot_be_reused(service):
    service.evidence.ttl = -1
    with pytest.raises(SourceError):
        await service.fetch("legifrance:" + ARTICLE)
