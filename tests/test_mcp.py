import os
import sys
from datetime import date

import pytest
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from droit_territorial.server import TOOL_NAMES, build_server


async def test_all_declared_tools_are_callable_and_read_only(service):
    server = build_server(service)
    tools = await server.list_tools()
    assert {t.name for t in tools} == TOOL_NAMES
    assert all(t.annotations.read_only_hint is True for t in tools)
    assert all(t.annotations.destructive_hint is False for t in tools)
    cases = {
        "search": {"query": "test", "as_of_date": "2026-09-15", "source_types": ["codes"]},
        "fetch": {"source_ref": "legifrance:LEGIARTI000000000001", "as_of_date": "2026-09-15"},
        "get_legal_version": {
            "text_ref": "Code de test",
            "article": "R2122-8",
            "as_of_date": "2026-09-15",
        },
        "compare_versions": {
            "text_ref": "Code de test",
            "article": "R2122-8",
            "from_date": "2026-05-01",
            "to_date": "2026-09-15",
        },
        "search_case_law": {"query": "test", "legal_order": "judicial"},
        "resolve_references": {
            "source_ref": "legifrance:LEGIARTI000000000001",
            "as_of_date": "2026-09-15",
        },
        "search_local_acts": {"query": "test", "case_id": "c"},
        "get_source_status": {},
        "search_admin_archive": {"query": "test", "courts": ["TA"]},
        "compare_evidence": {"before_id": "absent", "after_id": "absent"},
        "review_case": {
            "dossier": {
                "context": {
                    "case_id": "c",
                    "objective": "test",
                    "entity_type": "commune",
                    "actor_capacity": "maire",
                    "as_of_date": "2026-09-15",
                },
                "knowledge_cutoff": "2026-09-15T10:00:00Z",
                "qualifications": ["test"],
                "conclusion": "Non établi",
            }
        },
        "get_methodology": {"topic": "fpt"},
        "check_evidence": {
            "claims": [
                {"claim_id": "c", "statement": "test", "evidence_id": "invalid", "quote": "test"}
            ]
        },
        "evaluate_rule": {
            "rule_id": "procurement.dispense",
            "facts": {},
            "as_of_date": "2026-09-15",
        },
    }
    for name, arguments in cases.items():
        result = await server.call_tool(name, arguments)
        assert result.structured_content is not None, (name, result)
        assert result.structured_content.get("error", {}).get("code") != "internal_error", name


async def test_mcp_protocol_stdio_roundtrip():
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "droit_territorial.cli", "serve"],
        env={
            "PATH": os.environ.get("PATH", ""),
            "PISTE_CLIENT_ID": "",
            "PISTE_CLIENT_SECRET": "",
            "JUDILIBRE_KEY_ID": "",
            "JT_LOCAL_DB": "",
            "JT_EVIDENCE_DB": "",
            "JT_ADMIN_DB": "",
            "JT_PRINCIPAL": "",
        },
    )
    async with (
        stdio_client(params) as (read, write),
        ClientSession(read, write, read_timeout_seconds=15) as session,
    ):
        await session.initialize()
        tools = await session.list_tools()
        assert {tool.name for tool in tools.tools} == TOOL_NAMES
        method = await session.call_tool(
            "get_methodology", {"topic": "core", "output_mode": "short"}
        )
        assert not method.is_error and method.structured_content["method_version"] == "0.3.0"
        assert method.structured_content["text"]
        resource = await session.read_resource("juriste://methodology/core")
        assert resource.contents[0].text == method.structured_content["text"]
        prompts = await session.list_prompts()
        assert "analyse_territoriale" in {p.name for p in prompts.prompts}
        prompt = await session.get_prompt("analyse_territoriale", {"question": "Question fictive"})
        assert "Question fictive" in prompt.messages[0].content.text
        failed = await session.call_tool(
            "search", {"query": "temps de travail", "as_of_date": "2026-09-15"}
        )
        assert failed.is_error
        assert failed.structured_content["errors"][0]["code"] == "credentials_missing"


async def test_methodology_path_traversal_is_refused(service):
    result = await build_server(service).call_tool("get_methodology", {"topic": "../../.env"})
    assert result.is_error and result.structured_content["error"]["code"] == "unknown_topic"


async def test_status_does_not_expose_secrets(service):
    result = await build_server(service).call_tool("get_source_status", {})
    serialized = result.model_dump_json()
    assert service.settings.client_secret not in serialized
    assert service.settings.client_id not in serialized


@pytest.mark.live
@pytest.mark.skipif(
    os.getenv("JT_RUN_LIVE") != "1", reason="Live sources require explicit JT_RUN_LIVE=1"
)
async def test_live_legifrance_dated_article():
    from droit_territorial.runtime import Settings
    from droit_territorial.service import Service

    settings = Settings.from_env()
    if not settings.oauth_configured:
        pytest.skip("PISTE production credentials not configured")
    service = Service(settings)
    try:
        answer = await service.legal_version(
            "Code de la commande publique", "R2122-8", date(2026, 9, 15)
        )
        assert answer["status"] == "ok"
        assert "60 000" in answer["text"]
    finally:
        await service.close()
