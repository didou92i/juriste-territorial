"""Comparability and review accounting; supplied execution/reviewer identities are declarations."""

import hashlib
import json
import secrets
from collections import Counter
from statistics import median
from typing import Literal

from pydantic import Field, model_validator

from .models import Model


def fingerprint(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def verify_corpus_manifest(cases, raw: bytes, manifest: dict):
    """Require the private candidate corpus to match its public frozen hashes."""
    actual = {case["case_id"]: fingerprint(case) for case in cases}
    if (
        len(actual) != len(cases)
        or len(cases) != manifest.get("case_count")
        or actual != manifest.get("case_hashes")
        or hashlib.sha256(raw).hexdigest() != manifest.get("corpus_file_sha256")
    ):
        raise ValueError("Holdout corpus differs from its public frozen manifest")


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
    duration_ms: int | None = Field(default=None, ge=0)
    network_requests: int | None = Field(default=None, ge=0)
    reported_cost_eur: float | None = Field(default=None, ge=0)


class ReviewMetrics(Model):
    citation_errors: int = Field(ge=0)
    version_errors: int = Field(ge=0)
    case_law_relevance_errors: int = Field(ge=0)
    relevant_decisions_found: int = Field(ge=0)
    reference_decisions_total: int = Field(ge=0)
    missing_decisive_reservations: int = Field(ge=0)
    useful_reservations: int = Field(ge=0)
    unnecessary_questions: int = Field(ge=0)
    useful_action: bool

    @model_validator(mode="after")
    def consistent_decision_counts(self):
        if self.relevant_decisions_found > self.reference_decisions_total:
            raise ValueError("Relevant decisions found cannot exceed the reviewed reference set")
        return self


class Review(Model):
    run_id: str
    response_hash: str
    reviewer_id: str
    reviewer_kind: Literal["human_legal", "agent"]
    independent: bool
    critical_errors: list[str]
    findings: str = Field(min_length=1)
    metrics: ReviewMetrics | None = None


def prepare_review_packet(cases, runs: list[Run]):
    """Blind responses for human reviewers; the operator retains the separate key."""
    by_id = {case["case_id"]: case for case in cases}
    packet, key = [], {}
    for run in runs:
        case = by_id[run.case_id]
        if run.case_hash != fingerprint(case):
            raise ValueError(f"Case fingerprint mismatch: {run.run_id}")
        blind_id = secrets.token_hex(8)
        packet.append(
            {
                "blind_id": blind_id,
                "case_id": run.case_id,
                "prompt": case["prompt"],
                "pieces": case["pieces"],
                "knowledge_cutoff": case.get("knowledge_cutoff"),
                "response": run.response,
            }
        )
        key[blind_id] = {
            "run_id": run.run_id,
            "mode": run.mode,
            "response_hash": fingerprint(run.response),
        }
    secrets.SystemRandom().shuffle(packet)
    return packet, key


def benchmark(cases, runs: list[Run], reviews: list[Review]):
    ids = [r.run_id for r in runs]
    issues, pairs, holdout_triples = [], [], []
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
        holdout = by_case[case_id].get("split") == "private_holdout"
        repetitions = {r.repetition for r in runs if r.case_id == case_id} or {1}
        for repetition in sorted(repetitions):
            baseline = valid.get((case_id, repetition, "baseline"))
            skill = valid.get((case_id, repetition, "skill"))
            skill_mcp = valid.get((case_id, repetition, "skill_mcp"))
            if not baseline or not skill:
                issues.append(f"missing_pair:{case_id}:{repetition}")
                continue
            if holdout and not skill_mcp:
                issues.append(f"missing_mcp_arm:{case_id}:{repetition}")
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
            if holdout and any(
                getattr(baseline, f) != getattr(skill_mcp, f)
                for f in (
                    "model",
                    "model_version",
                    "parameters",
                    "research_budget",
                    "knowledge_cutoff",
                )
            ):
                issues.append(f"noncomparable_mcp_arm:{case_id}:{repetition}")
                continue
            human = {}
            arms = (baseline, skill, skill_mcp) if holdout else (baseline, skill)
            for run in arms:
                rows = [
                    r
                    for r in reviews
                    if r.run_id == run.run_id
                    and r.reviewer_kind == "human_legal"
                    and r.independent
                    and r.response_hash == fingerprint(run.response)
                ]
                minimum = 2 if holdout else 1
                if len({r.reviewer_id for r in rows}) < minimum:
                    issues.append("independent_human_review_missing:" + run.run_id)
                elif holdout and any(r.metrics is None for r in rows):
                    issues.append("review_metrics_missing:" + run.run_id)
                elif len({tuple(sorted(r.critical_errors)) for r in rows}) != 1 or (
                    holdout and len({r.metrics.model_dump_json() for r in rows}) != 1
                ):
                    issues.append("human_review_disagreement:" + run.run_id)
                else:
                    human[run.mode] = {
                        "critical_errors": len(rows[0].critical_errors),
                        "reviews": rows,
                        "run": run,
                    }
            if len(human) == len(arms):
                row = {
                    "case_id": case_id,
                    "repetition": repetition,
                    "critical_errors": {
                        mode: item["critical_errors"] for mode, item in human.items()
                    },
                }
                (holdout_triples if holdout else pairs).append(row)
    measured = {mode: [] for mode in ("baseline", "skill", "skill_mcp")}
    completed = {(r["case_id"], r["repetition"]) for r in holdout_triples}
    for run in runs:
        if (run.case_id, run.repetition) not in completed:
            continue
        rows = [r for r in reviews if r.run_id == run.run_id and r.metrics is not None]
        if len(rows) >= 2:
            measured[run.mode].append((run, rows[0]))
    summary = {}
    for mode, values in measured.items():
        if not values:
            continue
        durations = sorted(r.duration_ms for r, _ in values if r.duration_ms is not None)
        costs = [r.reported_cost_eur for r, _ in values]
        summary[mode] = {
            "runs": len(values),
            "critical_errors": sum(len(v.critical_errors) for _, v in values),
            "citation_errors": sum(v.metrics.citation_errors for _, v in values),
            "version_errors": sum(v.metrics.version_errors for _, v in values),
            "case_law_relevance_errors": sum(
                v.metrics.case_law_relevance_errors for _, v in values
            ),
            "relevant_decisions_found": sum(v.metrics.relevant_decisions_found for _, v in values),
            "reference_decisions_total": sum(
                v.metrics.reference_decisions_total for _, v in values
            ),
            "missing_decisive_reservations": sum(
                v.metrics.missing_decisive_reservations for _, v in values
            ),
            "useful_reservations": sum(v.metrics.useful_reservations for _, v in values),
            "unnecessary_questions": sum(v.metrics.unnecessary_questions for _, v in values),
            "useful_actions": sum(v.metrics.useful_action for _, v in values),
            "median_duration_ms": median(durations) if durations else None,
            "p95_duration_ms": durations[min(len(durations) - 1, int(len(durations) * 0.95))]
            if durations
            else None,
            "network_requests": sum(r.network_requests for r, _ in values)
            if all(r.network_requests is not None for r, _ in values)
            else None,
            "reported_cost_eur": round(sum(costs), 4)
            if all(value is not None for value in costs)
            else None,
        }
    return {
        "status": "incomplete"
        if issues or not (pairs or holdout_triples)
        else "declared_reviews_compared",
        "issues": issues,
        "complete_pairs": pairs,
        "complete_holdout_triples": holdout_triples,
        "holdout_metrics": summary,
        "run_artifact_hashes": {r.run_id: fingerprint(r.model_dump(mode="json")) for r in runs},
        "legal_validation": "not_certified",
        "reviewer_identity": "operator_declared_not_authenticated",
        "scope": "Public cases compare baseline/skill; private holdout requires three arms and two independent declared human reviews per run",
        "generalization": "Only private held-out cases can test unseen-case performance; reviewer identities remain operator declarations",
    }
