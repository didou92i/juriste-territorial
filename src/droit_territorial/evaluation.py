"""Comparability and review accounting; supplied execution/reviewer identities are declarations."""

import hashlib
import json
from collections import Counter
from typing import Literal

from pydantic import Field

from .models import Model


def fingerprint(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


class Run(Model):
    run_id: str
    case_id: str
    case_hash: str
    mode: Literal["baseline", "skill", "skill_mcp"]
    model: str = Field(min_length=1)
    model_version: str = Field(min_length=1)
    parameters: dict
    tools: list[str]
    research_budget: dict
    knowledge_cutoff: str
    method_hash: str | None = None
    repetition: int = Field(ge=1)
    response: str = Field(min_length=1)
    tool_events: list[dict]


class Review(Model):
    run_id: str
    response_hash: str
    reviewer_id: str
    reviewer_kind: Literal["human_legal", "agent"]
    independent: bool
    critical_errors: list[str]
    findings: str = Field(min_length=1)


def benchmark(cases, runs: list[Run], reviews: list[Review]):
    ids = [r.run_id for r in runs]
    issues, pairs = [], []
    if len(set(ids)) != len(ids):
        issues.append("duplicate_run_id")
    by_case = {c["case_id"]: c for c in cases}
    if len(by_case) != len(cases):
        issues.append("duplicate_case_id")
    valid = {}
    for run in runs:
        key = (run.case_id, run.repetition, run.mode)
        if key in valid:
            issues.append("duplicate_case_repetition_mode")
        valid[key] = run
        if run.case_id not in by_case or run.case_hash != fingerprint(by_case.get(run.case_id)):
            issues.append("case_hash_mismatch:" + run.run_id)
        if run.mode != "baseline" and not run.method_hash:
            issues.append("method_hash_missing:" + run.run_id)
    review_counts = Counter((r.run_id, r.reviewer_id) for r in reviews)
    if any(count > 1 for count in review_counts.values()):
        issues.append("duplicate_review")
    for row in reviews:
        candidates = [run for run in runs if run.run_id == row.run_id]
        if len(candidates) != 1 or fingerprint(candidates[0].response) != row.response_hash:
            issues.append("review_response_mismatch:" + row.run_id)
    for case_id in by_case:
        repetitions = {r.repetition for r in runs if r.case_id == case_id} or {1}
        for repetition in sorted(repetitions):
            baseline = valid.get((case_id, repetition, "baseline"))
            skill = valid.get((case_id, repetition, "skill"))
            if not baseline or not skill:
                issues.append(f"missing_pair:{case_id}:{repetition}")
                continue
            fields = (
                "model",
                "model_version",
                "parameters",
                "tools",
                "research_budget",
                "knowledge_cutoff",
            )
            if any(getattr(baseline, f) != getattr(skill, f) for f in fields):
                issues.append(f"noncomparable_pair:{case_id}:{repetition}")
                continue
            human = {}
            for run in (baseline, skill):
                rows = [
                    r
                    for r in reviews
                    if r.run_id == run.run_id
                    and r.reviewer_kind == "human_legal"
                    and r.independent
                    and r.response_hash == fingerprint(run.response)
                ]
                if not rows:
                    issues.append("independent_human_review_missing:" + run.run_id)
                elif len({tuple(r.critical_errors) for r in rows}) != 1:
                    issues.append("human_review_disagreement:" + run.run_id)
                else:
                    human[run.mode] = len(rows[0].critical_errors)
            if len(human) == 2:
                pairs.append(
                    {"case_id": case_id, "repetition": repetition, "critical_errors": human}
                )
    return {
        "status": "incomplete" if issues or not pairs else "declared_reviews_compared",
        "issues": issues,
        "complete_pairs": pairs,
        "run_artifact_hashes": {r.run_id: fingerprint(r.model_dump(mode="json")) for r in runs},
        "legal_validation": "not_certified",
        "reviewer_identity": "operator_declared_not_authenticated",
        "scope": "Paired baseline/skill within this corpus only; skill_mcp runs are retained separately, never pooled",
        "generalization": "Development cases are public and cannot demonstrate unseen-case performance",
    }
