from datetime import date

import pytest
from conftest import ARTICLE, article_payload
from pydantic import ValidationError

from droit_territorial.models import EndStatus, Fact, VersionInterval
from droit_territorial.sources import interval, normalise_legi, source_date


@pytest.mark.parametrize(
    "start,end,when,expected",
    [
        ("2026-04-01", "2999-01-01", "2026-09-15", "yes"),
        ("2026-04-01", "2999-01-01", "2026-03-31", "no"),
        ("2026-01-01", "2026-04-01", "2026-04-01", "no"),
        ("2026-01-01", "2026-04-01", "2026-03-31", "yes"),
        (None, "2999-01-01", "2026-04-01", "unknown"),
        ("2026-01-01", None, "2026-04-01", "unknown"),
        ("2026-01-01", "bad-date", "2026-04-01", "unknown"),
        ("2026-01-01", "2025-01-01", "2026-04-01", "unknown"),
        ("2026-01-01", "2999-01-01", None, "unknown"),
    ],
)
def test_time_uncertainty(start, end, when, expected):
    assert interval(start, end).at(date.fromisoformat(when) if when else None) == expected


@pytest.mark.parametrize(
    "kwargs",
    [
        {"end_status": "known"},
        {"end": "2026-01-01", "end_status": "open"},
        {"start": "2026-04-01", "end": "2026-04-01", "end_status": "known"},
    ],
)
def test_invalid_version_states_refused(kwargs):
    with pytest.raises(ValidationError):
        VersionInterval(**kwargs)


def test_invalid_end_never_open():
    assert interval("2026-01-01", "bad").end_status == EndStatus.INVALID
    assert source_date(True) is None


def test_established_fact_needs_piece():
    with pytest.raises(ValidationError):
        Fact(fact_id="f1", statement="Délégation existante", status="established")


def test_official_authenticity_not_applicability():
    doc = normalise_legi(article_payload(start=None), ARTICLE)
    assert doc.source_authenticity == "official"
    assert doc.version.at(date(2026, 9, 15)) == "unknown"
