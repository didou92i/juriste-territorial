"""Domain vocabulary. Authenticity never implies applicability or legal validity."""

from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class LegalOrder(StrEnum):
    ADMINISTRATIVE = "administrative"
    JUDICIAL = "judicial"
    ANY = "any"


class EndStatus(StrEnum):
    KNOWN = "known"
    OPEN = "open"
    MISSING = "missing"
    INVALID = "invalid"


class VersionInterval(Model):
    start: date | None = None
    end: date | None = None
    end_status: EndStatus = EndStatus.MISSING

    @model_validator(mode="after")
    def consistent(self):
        if (self.end_status == EndStatus.KNOWN) != (self.end is not None):
            raise ValueError("A known end requires a date; other end states must not carry one")
        if self.start and self.end and self.end <= self.start:
            raise ValueError("Version end must be later than start (exclusive end)")
        return self

    def at(self, when: date | None) -> Literal["yes", "no", "unknown"]:
        if when is None:
            return "unknown"
        if self.start and when < self.start:
            return "no"
        if self.end and when >= self.end:
            return "no"
        if self.start is None or self.end_status in {EndStatus.MISSING, EndStatus.INVALID}:
            return "unknown"
        return "yes"


class Fact(Model):
    fact_id: str = Field(min_length=1, max_length=100)
    statement: str = Field(min_length=1, max_length=6000)
    status: Literal["established", "declared", "contested", "inferred", "missing"]
    piece_refs: list[str] = Field(default_factory=list, max_length=50)

    @model_validator(mode="after")
    def established_has_piece(self):
        if self.status == "established" and not self.piece_refs:
            raise ValueError("An established fact requires a piece reference")
        return self


class CaseContext(Model):
    case_id: str = Field(min_length=1, max_length=100)
    objective: str = Field(min_length=1, max_length=6000)
    entity_type: str
    actor_capacity: str
    as_of_date: date
    method_version: str = "0.1.0"
    facts: list[Fact] = Field(default_factory=list, max_length=200)
    event_dates: dict[str, date] = Field(default_factory=dict)


class Document(Model):
    provider: str = Field(min_length=1)
    canonical_id: str = Field(min_length=1)
    canonical_url: str | None = None
    title: str
    text: str = Field(min_length=1, max_length=2_000_000)
    document_kind: str
    legal_order: LegalOrder = LegalOrder.ANY
    court_or_issuer: str | None = None
    source_authenticity: Literal["official", "institutional", "secondary", "unknown"]
    published_at: date | None = None
    decision_date: date | None = None
    signed_at: date | None = None
    source_updated_at: str | None = None
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    version: VersionInterval = Field(default_factory=VersionInterval)
    source_complete: bool = False
    truncation_reason: str | None = None
    territorial_scope: str | None = None
    material_scope: str | None = None
    reuse_policy: str = "Consult provider terms before redistribution"
    access_scope: str = "public"
    case_id: str | None = None
    withdrawal_status: Literal["not_checked", "not_reported", "withdrawn"] = "not_checked"
    related_refs: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class Evidence(Model):
    evidence_id: str
    source_ref: str
    document: Document
    content_hash: str
    as_of_date: date | None


class ClaimInput(Model):
    claim_id: str = Field(min_length=1, max_length=100)
    statement: str = Field(min_length=1, max_length=6000)
    evidence_id: str = Field(min_length=1, max_length=100)
    quote: str = Field(min_length=1, max_length=4000)
    as_of_date: date | None = None
    fact_ids: list[str] = Field(default_factory=list, max_length=50)


class Problem(Model):
    code: str
    message: str
    provider: str | None = None
    retryable: bool = False


class SourceError(Exception):
    def __init__(self, code: str, message: str, provider: str | None = None, retryable=False):
        self.problem = Problem(code=code, message=message, provider=provider, retryable=retryable)
        super().__init__(message)


def problem(code: str, message: str, provider: str | None = None) -> dict:
    return {
        "status": "error",
        "error": Problem(code=code, message=message, provider=provider).model_dump(),
    }
