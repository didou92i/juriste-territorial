from droit_territorial.evaluation import Review, Run, benchmark, fingerprint

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
