"""Ephemeral server-issued snapshots. Caller-provided ids never create provenance."""

import hashlib
import time
import uuid
from collections import OrderedDict
from datetime import date

from .models import ClaimInput, Document, Evidence, SourceError


class EvidenceStore:
    def __init__(self, max_entries=32, ttl=1800, archive=None):
        self.entries = OrderedDict()
        self.max_entries, self.ttl = max_entries, ttl
        self.archive = archive

    def put(self, source_ref: str, doc: Document, as_of: date | None):
        identifier = "ev_" + uuid.uuid4().hex
        evidence = Evidence(
            evidence_id=identifier,
            source_ref=source_ref,
            document=doc.model_copy(deep=True),
            content_hash=hashlib.sha256(doc.text.encode()).hexdigest(),
            as_of_date=as_of,
        )
        if self.archive:
            self.archive.put("evidence", evidence.model_dump(mode="json"), identifier)
        self.entries[identifier] = (time.monotonic(), evidence)
        while len(self.entries) > self.max_entries:
            self.entries.popitem(last=False)
        return evidence

    def get(self, identifier):
        item = self.entries.get(identifier)
        if item is None or time.monotonic() - item[0] > self.ttl:
            self.entries.pop(identifier, None)
            if self.archive:
                ev = Evidence.model_validate(self.archive.get("evidence", identifier))
                if hashlib.sha256(ev.document.text.encode()).hexdigest() != ev.content_hash:
                    raise SourceError("archive_corrupted", "Evidence content hash mismatch")
                return ev
            raise SourceError(
                "evidence_unavailable", "Evidence absent or expired; fetch the source again"
            )
        return item[1]

    def page(self, identifier, offset=0, length=6000):
        ev = self.get(identifier)
        text = ev.document.text
        if offset < 0 or offset >= len(text):
            raise SourceError("invalid_offset", "Offset is outside the retrieved document")
        end = min(offset + length, len(text))
        metadata = ev.document.model_dump(mode="json", exclude={"text", "locators"})
        locators = [
            item.model_dump(mode="json")
            for item in ev.document.locators
            if item.start < end and item.end > offset
        ]
        return {
            "status": "ok",
            "evidence_id": identifier,
            "source_ref": "evidence:" + identifier,
            "original_source_ref": ev.source_ref,
            "metadata": metadata,
            "as_of_date": ev.as_of_date.isoformat() if ev.as_of_date else None,
            "temporal_applicability": ev.document.version.at(ev.as_of_date),
            "temporal_scope": "Version interval only; transitions and factual applicability need review",
            "content_hash": ev.content_hash,
            "text": text[offset:end],
            "excerpt_locator": f"chars:{offset}:{end}",
            "source_locators": locators,
            "next_offset": end if end < len(text) else None,
            "total_characters": len(text),
            "response_complete": offset == 0 and end == len(text),
            "content_trust": "untrusted_data",
            "legal_validity": "not_assessed",
        }

    def check(self, claim: ClaimInput):
        ev = self.get(claim.evidence_id)
        issues = []
        position = ev.document.text.find(claim.quote)
        locator = next(
            (
                item.label
                for item in ev.document.locators
                if position >= item.start and position < item.end
            ),
            None,
        )
        if position < 0:
            issues.append("quote_not_in_retrieved_text")
        if not ev.document.source_complete:
            issues.append("source_completeness_not_established")
        when = claim.as_of_date or ev.as_of_date
        temporal = ev.document.version.at(when)
        if ev.document.document_kind in {"article", "text", "local_act"} and temporal != "yes":
            issues.append("temporal_applicability_" + temporal)
        if ev.document.source_authenticity not in {"official", "institutional"}:
            issues.append("authenticity_not_established")
        return {
            "claim_id": claim.claim_id,
            "evidence_id": ev.evidence_id,
            "status": "technical_check_only",
            "technical_issues": issues,
            "quote_found": position >= 0,
            "quote_offset": position if position >= 0 else None,
            "source_locator": locator,
            "content_hash": ev.content_hash,
            "source_ref": ev.source_ref,
            "temporal_applicability": temporal,
            "legal_validity": "not_assessed",
            "semantic_support": "not_assessed",
            "fact_ids": claim.fact_ids,
            "remaining_review": "Relevance, conditions, facts, party/judge attribution, exceptions and operative conclusion",
        }
