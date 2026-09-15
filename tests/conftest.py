"""Synthetic fixtures: identifiers/text below are not real legal citations."""

import json

import httpx
import pytest

from droit_territorial.runtime import Settings, Transport
from droit_territorial.service import Service

ARTICLE = "LEGIARTI000000000001"
ARTICLE2 = "LEGIARTI000000000002"
DECISION = "CETATEXT000000000003"
JUDICIAL = "a" * 24
BODY = "Disposition fictive pour tests. L'autorité peut agir sous la condition A. Exception : B."


def article_payload(identifier=ARTICLE, start="2026-04-01", end="2999-01-01", body=BODY):
    return {
        "article": {
            "id": identifier,
            "num": "R2122-8",
            "texte": body,
            "dateDebut": start,
            "dateFin": end,
        }
    }


def search_payload(identifier=ARTICLE, number="R2122-8", total=1):
    return {
        "totalResultNumber": total,
        "results": [
            {
                "titles": [{"id": "LEGITEXT000000000004", "title": "Code de test"}],
                "sections": [
                    {"extracts": [{"id": identifier, "num": number, "texte": "Extrait fictif"}]}
                ],
            }
        ],
    }


@pytest.fixture
def api_handler():
    def handler(request):
        if "oauth" in request.url.host:
            return httpx.Response(200, json={"access_token": "synthetic-token", "expires_in": 3600})
        if request.url.path.endswith("getArticle"):
            identifier = json.loads(request.content)["id"]
            return httpx.Response(200, json=article_payload(identifier))
        if request.url.path.endswith("/taxonomy"):
            return httpx.Response(
                200, json={"result": {"cc": "Cour de cassation", "ca": "Cour d'appel"}}
            )
        if request.url.path.endswith("/decision"):
            return httpx.Response(
                200,
                json={
                    "id": JUDICIAL,
                    "text": BODY,
                    "jurisdiction": "cc",
                    "decision_date": "2026-02-01",
                },
            )
        if request.url.path.endswith("/search"):
            if "judilibre" in request.url.path:
                return httpx.Response(
                    200, json={"results": [{"id": JUDICIAL, "jurisdiction": "cc"}], "total": 1}
                )
            return httpx.Response(200, json=search_payload())
        return httpx.Response(404)

    return handler


@pytest.fixture
async def service(api_handler):
    settings = Settings(client_id="synthetic-client", client_secret="synthetic-secret")
    transport = Transport(settings, httpx.AsyncClient(transport=httpx.MockTransport(api_handler)))
    instance = Service(settings, transport)
    try:
        yield instance
    finally:
        await instance.close()
