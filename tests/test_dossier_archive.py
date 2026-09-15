import hashlib
import sqlite3
from datetime import UTC, date, datetime, timedelta

import pytest

from droit_territorial.archive import Archive
from droit_territorial.dossier import Dossier
from droit_territorial.evidence import EvidenceStore
from droit_territorial.local import import_document, withdraw_document
from droit_territorial.models import Document, SourceError
from droit_territorial.runtime import Settings
from droit_territorial.service import Service


def document(**kwargs):
    return Document(
        provider="fixture",
        canonical_id="rule",
        title="Fictitious rule",
        text="Le conseil autorise cette aide. Le devis est joint.",
        document_kind="article",
        source_authenticity="official",
        source_complete=True,
        version={"start": "2026-01-01", "end_status": "open"},
        **kwargs,
    )


def dossier(service):
    ev = service.evidence.put("fixture:rule", document(), date(2026, 9, 15))
    value = {
        "context": {
            "case_id": "c1",
            "objective": "Analyser",
            "entity_type": "syndicat",
            "actor_capacity": "bureau",
            "as_of_date": "2026-09-15",
            "facts": [
                {
                    "fact_id": "f1",
                    "statement": "Le devis est joint.",
                    "status": "established",
                    "piece_refs": ["p1"],
                }
            ],
        },
        "knowledge_cutoff": datetime.now(UTC).isoformat(),
        "qualifications": ["aide privée"],
        "pieces": [
            {
                "piece_id": "p1",
                "evidence_id": ev.evidence_id,
                "expected_hash": ev.content_hash,
                "role": "rule",
            }
        ],
        "conditions": [
            {
                "condition_id": "c1",
                "question": "Pouvoir ?",
                "rule": {
                    "claim_id": "r1",
                    "statement": "Compétence",
                    "quote": "Le conseil autorise cette aide.",
                    "evidence_id": ev.evidence_id,
                    "as_of_date": "2026-09-15",
                    "fact_ids": ["f1"],
                },
                "assessment": "met",
                "application": "Motivation de test",
                "objection": "Vote à examiner",
                "consequence": "Instruction possible",
                "next_action": "Relire le vote",
            }
        ],
        "conclusion": "Position motivée fictive",
    }
    return Dossier.model_validate(value)


def codes(report):
    return {item["code"] for item in report["issues"]}


async def test_no_issue_is_never_legal_approval(service):
    value = dossier(service)
    report = service.review_case(value)
    assert report["issues"] == []
    assert report["legal_validity"] == report["semantic_support"] == "not_assessed"
    # A structurally complete but semantically unsupported assertion remains unassessed.
    value.conditions[0].rule.statement = "Le maire peut tout signer sans délégation."
    assert service.review_case(value)["semantic_support"] == "not_assessed"


@pytest.mark.parametrize(
    "mutation,expected",
    [
        (lambda d: setattr(d.pieces[0], "expected_hash", "0" * 64), "piece_version_mismatch"),
        (lambda d: setattr(d.context.facts[0], "piece_refs", ["absent"]), "fact_piece_unverified"),
        (
            lambda d: setattr(d.context.facts[0], "status", "contested"),
            "condition_relies_on_unestablished_fact",
        ),
        (
            lambda d: setattr(d.conditions[0].rule, "quote", "Citation inventée"),
            "quote_not_in_retrieved_text",
        ),
        (lambda d: setattr(d.conditions[0].rule, "fact_ids", ["absent"]), "fact_reference_missing"),
        (lambda d: setattr(d.conditions[0].rule, "as_of_date", None), "rule_trigger_date_missing"),
        (lambda d: setattr(d, "qualification_disputed", True), "competing_qualification_missing"),
        (lambda d: setattr(d.pieces[0], "role", "case_law"), "decision_analysis_missing"),
        (
            lambda d: setattr(d, "knowledge_cutoff", datetime.now(UTC) - timedelta(days=1)),
            "evidence_after_knowledge_cutoff",
        ),
        (lambda d: d.pieces.append(d.pieces[0]), "duplicate_id"),
    ],
)
async def test_decisive_gaps_are_visible(service, mutation, expected):
    value = dossier(service)
    mutation(value)
    assert expected in codes(service.review_case(value))


async def test_missing_annex_and_ground_are_distinct(service):
    value = dossier(service).model_dump()
    value["relations"] = [
        {"source": "p1", "target": "annex", "kind": "annex_to", "quote": "Le devis est joint."}
    ]
    value["grounds"] = [
        {
            "ground_id": "g",
            "kind": "competence",
            "condition_ids": ["absent"],
            "proposed_effect": "À déterminer",
            "effect_limits": "Pièce absente",
        }
    ]
    assert codes(service.review_case(Dossier.model_validate(value))) >= {
        "relation_piece_unverified",
        "ground_condition_missing",
    }


def test_archive_survives_restart_and_filters_principal(tmp_path):
    path = str(tmp_path / "evidence.sqlite")
    store = EvidenceStore(ttl=-1, archive=Archive(path, "alice"))
    ev = store.put("fixture:rule", document(), None)
    assert EvidenceStore(archive=Archive(path, "alice")).get(ev.evidence_id) == ev
    with pytest.raises(SourceError, match="unavailable"):
        EvidenceStore(archive=Archive(path, "bob")).get(ev.evidence_id)
    assert (tmp_path / "evidence.sqlite").stat().st_mode & 0o777 == 0o600
    with sqlite3.connect(path) as db:
        db.execute("UPDATE snapshots SET body='{}'")
    with pytest.raises(SourceError, match="integrity"):
        store.get(ev.evidence_id)


def test_archive_refuses_symlink(tmp_path):
    target = tmp_path / "actual"
    target.write_text("untouched")
    link = tmp_path / "link"
    link.symlink_to(target)
    with pytest.raises(OSError):
        Archive(str(link), "alice")
    assert target.read_text() == "untouched"


async def test_private_case_boundary_and_withdrawal_survive_restart(tmp_path):
    local_db = tmp_path / "local.sqlite"
    file = tmp_path / "piece.txt"
    file.write_text("Le conseil autorise cette aide.")
    identifier = import_document(local_db, file, "alice", "other-case", "Private")
    settings = Settings(
        local_db=str(local_db), principal="alice", evidence_db=str(tmp_path / "ev.sqlite")
    )
    service = Service(settings)
    try:
        value = dossier(service)
        fetched = await service.fetch("local:" + identifier)
        value.pieces[0].evidence_id = fetched["evidence_id"]
        value.pieces[0].expected_hash = fetched["content_hash"]
        assert "piece_outside_case" in codes(service.review_case(value))
        value.context.case_id = "other-case"
        record = service.record_case(value)
    finally:
        await service.close()
    service = Service(settings)
    try:
        assert service.read_case(record["record_id"])["status"] == "historical_record"
        withdraw_document(local_db, "alice", identifier)
        with pytest.raises(SourceError):
            service.read_case(record["record_id"])
        with pytest.raises(SourceError):
            await service.fetch("evidence:" + fetched["evidence_id"])
    finally:
        await service.close()


async def test_comparison_preserves_original_and_detects_metadata(service):
    old = service.evidence.put("fixture:rule", document(), None)
    doc = document()
    doc.source_updated_at = "2026-09-16"
    new = service.evidence.put("fixture:rule", doc, None)
    result = service.compare_evidence(old.evidence_id, new.evidence_id)
    assert result["reexamination_required"] and result["metadata_changed"]
    assert not result["content_changed"] and not result["historical_record_modified"]
    assert old.content_hash == hashlib.sha256(old.document.text.encode()).hexdigest()
