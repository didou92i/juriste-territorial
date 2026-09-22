"""Review an explicit justification graph; never grade the truth of a legal conclusion."""

from datetime import date, datetime
from typing import Literal

from pydantic import Field

from .models import CaseContext, ClaimInput, Model, SourceError

Text = str


class Piece(Model):
    piece_id: str = Field(min_length=1, max_length=100)
    evidence_id: str
    expected_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    role: Literal["rule", "case_law", "local_act", "fact"]


class Relation(Model):
    source: str
    target: str
    kind: Literal["annex_to", "delegates", "approves", "implements", "replaces", "cites"]
    quote: str = Field(min_length=1, max_length=4000)


class Condition(Model):
    condition_id: str
    question: str = Field(min_length=1, max_length=6000)
    rule: ClaimInput
    application: str = Field(min_length=1, max_length=6000)
    assessment: Literal["met", "not_met", "unknown", "disputed"]
    objection: str = Field(min_length=1, max_length=6000)
    consequence: str = Field(min_length=1, max_length=6000)
    next_action: str = Field(min_length=1, max_length=6000)
    decisive: bool = False
    prerequisite_mode: Literal["all", "any"] = "all"
    prerequisite_ids: list[str] = Field(default_factory=list, max_length=50)
    exception_to: str | None = None


class QualificationBranch(Model):
    qualification: str = Field(min_length=1, max_length=6000)
    condition_ids: list[str] = Field(min_length=1, max_length=50)
    possible_outcome: str = Field(min_length=1, max_length=6000)


class DecisionSheet(Model):
    competent_authority: str = Field(min_length=1, max_length=6000)
    authority_condition_id: str
    trigger_date: date
    trigger_date_reason: str = Field(min_length=1, max_length=6000)
    branches: list[QualificationBranch] = Field(min_length=1, max_length=10)
    strongest_objection_condition_id: str
    flip_fact_ids: list[str] = Field(min_length=1, max_length=50)
    next_action: str = Field(min_length=1, max_length=6000)


class Ground(Model):
    ground_id: str
    kind: Literal["admissibility", "competence", "procedure", "merits", "evidence"]
    condition_ids: list[str] = Field(min_length=1, max_length=50)
    proposed_effect: str = Field(min_length=1, max_length=6000)
    effect_limits: str = Field(min_length=1, max_length=6000)


class DecisionAnalysis(Model):
    piece_id: str
    procedural_stage: Literal["interim", "merits", "admission", "other", "unknown"]
    party_argument: str = Field(min_length=1, max_length=6000)
    judge_quote: str = Field(min_length=1, max_length=4000)
    holding: str = Field(min_length=1, max_length=6000)
    operative_effect: str = Field(min_length=1, max_length=6000)
    transposition_limits: str = Field(min_length=1, max_length=6000)
    adverse_authority_search: str = Field(min_length=1, max_length=6000)


class Dossier(Model):
    context: CaseContext
    knowledge_cutoff: datetime
    qualifications: list[str] = Field(min_length=1, max_length=10)
    qualification_disputed: bool = False
    pieces: list[Piece] = Field(default_factory=list, max_length=200)
    relations: list[Relation] = Field(default_factory=list, max_length=200)
    conditions: list[Condition] = Field(default_factory=list, max_length=100)
    grounds: list[Ground] = Field(default_factory=list, max_length=100)
    decisions: list[DecisionAnalysis] = Field(default_factory=list, max_length=100)
    decision_sheet: DecisionSheet | None = None
    conclusion_status: Literal["established", "conditional", "not_established"] = "conditional"
    conclusion: str = Field(min_length=1, max_length=12000)
    reservations: list[str] = Field(default_factory=list, max_length=50)


def review(dossier: Dossier, service):
    issues, checked = [], {}

    def flag(code, ref):
        issues.append({"code": code, "ref": ref})

    def indexed(items, attribute):
        result = {}
        for item in items:
            key = getattr(item, attribute)
            if key in result:
                flag("duplicate_id", key)
            result[key] = item
        return result

    pieces = indexed(dossier.pieces, "piece_id")
    facts = indexed(dossier.context.facts, "fact_id")
    conditions = indexed(dossier.conditions, "condition_id")
    indexed(dossier.grounds, "ground_id")
    if dossier.knowledge_cutoff.tzinfo is None:
        flag("knowledge_cutoff_timezone_missing", "dossier")
    if dossier.qualification_disputed and len(set(dossier.qualifications)) < 2:
        flag("competing_qualification_missing", "dossier")
    if not conditions:
        flag("decisive_conditions_missing", "dossier")
    if dossier.context.risk_level == "sensitive" and dossier.decision_sheet is None:
        flag("sensitive_decision_sheet_missing", "dossier")
    for piece in pieces.values():
        try:
            ev = service.evidence.get(piece.evidence_id)
            service._check_snapshot_access(ev)
            if (
                ev.document.access_scope != "public"
                and ev.document.case_id != dossier.context.case_id
            ):
                flag("piece_outside_case", piece.piece_id)
                continue
            if ev.content_hash != piece.expected_hash:
                flag("piece_version_mismatch", piece.piece_id)
                continue
            checked[piece.piece_id] = ev
            if (
                dossier.knowledge_cutoff.tzinfo
                and ev.document.retrieved_at > dossier.knowledge_cutoff
            ):
                flag("evidence_after_knowledge_cutoff", piece.piece_id)
        except SourceError as exc:
            flag(exc.problem.code, piece.piece_id)
    for fact in facts.values():
        for ref in fact.piece_refs:
            if ref not in checked:
                flag("fact_piece_unverified", fact.fact_id)
    replacements = {}
    for relation in dossier.relations:
        if relation.source not in checked or relation.target not in checked:
            flag("relation_piece_unverified", relation.source)
            continue
        if relation.quote not in checked[relation.source].document.text:
            flag("relation_quote_missing", relation.source)
        if relation.kind == "replaces":
            replacements[relation.source] = relation.target
            old = checked[relation.target].document
            new = checked[relation.source].document
            if old.signed_at and new.signed_at and new.signed_at < old.signed_at:
                flag("replacement_chronology_conflict", relation.source)
    for start in replacements:
        seen, node = set(), start
        while node in replacements:
            if node in seen:
                flag("replacement_cycle", start)
                break
            seen.add(node)
            node = replacements[node]
    claim_checks = []
    verified_evidence = {ev.evidence_id for ev in checked.values()}
    for condition in conditions.values():
        claim = condition.rule
        if claim.evidence_id not in verified_evidence:
            flag("rule_piece_unverified", condition.condition_id)
        else:
            result = service.evidence.check(claim)
            claim_checks.append(result)
            for code in result["technical_issues"]:
                flag(code, condition.condition_id)
        if claim.as_of_date is None:
            flag("rule_trigger_date_missing", condition.condition_id)
        elif claim.as_of_date not in {
            dossier.context.as_of_date,
            *dossier.context.event_dates.values(),
        }:
            flag("rule_trigger_date_unexplained", condition.condition_id)
        if not claim.fact_ids:
            flag("application_facts_missing", condition.condition_id)
        for fact_id in claim.fact_ids:
            if fact_id not in facts:
                flag("fact_reference_missing", condition.condition_id)
            elif facts[fact_id].status != "established" and condition.assessment == "met":
                flag("condition_relies_on_unestablished_fact", condition.condition_id)
        if condition.assessment in {"unknown", "disputed"} and not dossier.reservations:
            flag("unresolved_condition_without_reservation", condition.condition_id)
        for ref in condition.prerequisite_ids:
            if ref not in conditions:
                flag("condition_prerequisite_missing", condition.condition_id)
            elif ref == condition.condition_id:
                flag("condition_dependency_cycle", condition.condition_id)
        prerequisites = [conditions[ref] for ref in condition.prerequisite_ids if ref in conditions]
        if condition.assessment == "met" and prerequisites:
            if condition.prerequisite_mode == "all" and any(
                item.assessment != "met" for item in prerequisites
            ):
                flag("declared_dependency_conflict", condition.condition_id)
            if condition.prerequisite_mode == "any" and all(
                item.assessment != "met" for item in prerequisites
            ):
                flag("declared_dependency_conflict", condition.condition_id)
        if condition.exception_to and condition.exception_to not in conditions:
            flag("exception_target_missing", condition.condition_id)
        elif condition.exception_to == condition.condition_id:
            flag("exception_self_reference", condition.condition_id)
    visited, active = set(), set()

    def check_cycle(identifier):
        if identifier in active:
            flag("condition_dependency_cycle", identifier)
            return
        if identifier in visited or identifier not in conditions:
            return
        active.add(identifier)
        for ref in conditions[identifier].prerequisite_ids:
            check_cycle(ref)
        active.remove(identifier)
        visited.add(identifier)

    for identifier in conditions:
        check_cycle(identifier)
    if dossier.conclusion_status == "established" and any(
        c.decisive and c.assessment in {"unknown", "disputed"} for c in conditions.values()
    ):
        flag("certainty_with_unresolved_decisive_condition", "dossier")
    sheet = dossier.decision_sheet
    if sheet:
        if sheet.authority_condition_id not in conditions:
            flag("authority_condition_missing", "decision_sheet")
        if sheet.strongest_objection_condition_id not in conditions:
            flag("objection_condition_missing", "decision_sheet")
        if sheet.trigger_date not in {
            dossier.context.as_of_date,
            *dossier.context.event_dates.values(),
        }:
            flag("trigger_date_unexplained", "decision_sheet")
        if dossier.qualification_disputed and len({b.qualification for b in sheet.branches}) < 2:
            flag("competing_branch_missing", "decision_sheet")
        covered = set()
        for branch in sheet.branches:
            if branch.qualification not in dossier.qualifications:
                flag("branch_qualification_unknown", branch.qualification)
            for ref in branch.condition_ids:
                if ref not in conditions:
                    flag("branch_condition_missing", branch.qualification)
                covered.add(ref)
        for condition in conditions.values():
            if condition.decisive and condition.condition_id not in covered:
                flag("decisive_condition_unmapped", condition.condition_id)
        for ref in sheet.flip_fact_ids:
            if ref not in facts:
                flag("flip_fact_missing", ref)
    for ground in dossier.grounds:
        for ref in ground.condition_ids:
            if ref not in conditions:
                flag("ground_condition_missing", ground.ground_id)
    analyzed = {item.piece_id for item in dossier.decisions}
    for piece in pieces.values():
        if piece.role == "case_law" and piece.piece_id not in analyzed:
            flag("decision_analysis_missing", piece.piece_id)
    for decision in dossier.decisions:
        ev = checked.get(decision.piece_id)
        if ev is None or decision.judge_quote not in ev.document.text:
            flag("judge_quote_unverified", decision.piece_id)
        if decision.procedural_stage == "unknown":
            flag("decision_stage_unknown", decision.piece_id)
    return {
        "status": "technical_check_only",
        "issues": issues,
        "claim_checks": claim_checks,
        "legal_validity": "not_assessed",
        "semantic_support": "not_assessed",
        "assertions": "Qualifications, factual proof, attribution, grounds and effects are analyst assertions",
        "scope": "References, literal quotes, dates and declared structure only; no approval to act",
    }
