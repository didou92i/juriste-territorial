import pytest

from droit_territorial.evaluation import (
    Review,
    ReviewMetrics,
    Run,
    benchmark,
    fingerprint,
    prepare_review_packet,
    verify_corpus_manifest,
)

CASE = {"case_id": "synthetic", "prompt": "Test", "pieces": []}


def runs():
    values = []
    for mode in ("baseline", "skill"):
        values.append(
            Run(
                run_id=mode,
                case_id="synthetic",
                case_hash=fingerprint(CASE),
                mode=mode,
                model="test-model",
                model_version="fixed",
                parameters={"temperature": 0},
                tools=["official_search"],
                research_budget={"calls": 10},
                knowledge_cutoff="2026-09-15",
                method_hash="hash" if mode == "skill" else None,
                repetition=1,
                response="Fictitious answer",
                tool_events=[],
            )
        )
    return values


def reviews(values, kind="human_legal"):
    return [
        Review(
            run_id=r.run_id,
            response_hash=fingerprint(r.response),
            reviewer_id="declared-reviewer",
            reviewer_kind=kind,
            independent=True,
            critical_errors=[],
            findings="Fictitious review",
        )
        for r in values
    ]


def test_empty_campaign_cannot_be_success():
    result = benchmark([CASE], [], [])
    assert result["status"] == "incomplete" and result["complete_pairs"] == []


def test_agent_review_never_counts_as_human_validation():
    values = runs()
    result = benchmark([CASE], values, reviews(values, "agent"))
    assert result["status"] == "incomplete" and not result["complete_pairs"]


def test_changed_tool_budget_or_model_blocks_comparison():
    for field, value in (
        ("tools", ["different"]),
        ("research_budget", {"calls": 100}),
        ("model_version", "new"),
    ):
        values = runs()
        setattr(values[1], field, value)
        assert benchmark([CASE], values, reviews(values))["status"] == "incomplete"


def test_tampered_corpus_or_response_invalidates_review():
    values = runs()
    annotations = reviews(values)
    values[0].response = "Different answer"
    result = benchmark([CASE], values, annotations)
    assert result["status"] == "incomplete"
    assert any("review_response_mismatch" in x for x in result["issues"])
    values = runs()
    values[0].case_hash = "wrong"
    assert benchmark([CASE], values, reviews(values))["status"] == "incomplete"


def test_declared_human_comparison_is_not_certified():
    values = runs()
    result = benchmark([CASE], values, reviews(values))
    assert result["status"] == "declared_reviews_compared"
    assert result["legal_validation"] == "not_certified"
    assert result["reviewer_identity"] == "operator_declared_not_authenticated"


def test_private_holdout_requires_three_arms_and_two_matching_human_reviews():
    case = {**CASE, "split": "private_holdout"}
    values = runs()
    for row in values:
        row.case_hash = fingerprint(case)
        row.duration_ms = 100
        row.network_requests = 2
    mcp = values[1].model_copy(deep=True)
    mcp.run_id = "mcp"
    mcp.mode = "skill_mcp"
    values.append(mcp)
    assert "missing_mcp_arm" in str(benchmark([case], values[:2], []))
    metrics = ReviewMetrics(
        citation_errors=0,
        version_errors=0,
        case_law_relevance_errors=0,
        relevant_decisions_found=0,
        reference_decisions_total=0,
        missing_decisive_reservations=0,
        useful_reservations=0,
        unnecessary_questions=0,
        useful_action=True,
    )
    assessments = [
        Review(
            run_id=row.run_id,
            response_hash=fingerprint(row.response),
            reviewer_id=reviewer,
            reviewer_kind="human_legal",
            independent=True,
            critical_errors=[],
            findings="Fictitious review",
            metrics=metrics.model_copy(deep=True),
        )
        for row in values
        for reviewer in ("jurist-a", "jurist-b")
    ]
    result = benchmark([case], values, assessments)
    assert result["status"] == "declared_reviews_compared"
    assert len(result["complete_holdout_triples"]) == 1
    assert result["holdout_metrics"]["skill_mcp"]["median_duration_ms"] == 100
    assessments[1].metrics.citation_errors = 1
    assert "human_review_disagreement" in str(benchmark([case], values, assessments))


def test_reviewer_packet_does_not_reveal_mode_or_tool_trace():
    packet, operator_key = prepare_review_packet([CASE], runs())
    assert len(packet) == len(operator_key) == 2
    assert all("mode" not in row and "tool_events" not in row for row in packet)
    assert {row["mode"] for row in operator_key.values()} == {"baseline", "skill"}


def test_private_corpus_manifest_detects_changes():
    import hashlib

    raw = b'{"case_id":"synthetic","prompt":"Test","pieces":[]}\n'
    manifest = {
        "case_count": 1,
        "case_hashes": {"synthetic": fingerprint(CASE)},
        "corpus_file_sha256": hashlib.sha256(raw).hexdigest(),
    }
    verify_corpus_manifest([CASE], raw, manifest)
    with pytest.raises(ValueError):
        verify_corpus_manifest([{**CASE, "prompt": "Changed"}], raw, manifest)
