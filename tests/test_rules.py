from datetime import date

import pytest

from droit_territorial.models import SourceError
from droit_territorial.rules import evaluate


def facts(amount="50000", when="2026-04-01", kind="supplies", **changes):
    return {
        "buyer_type": "other_contracting_authority",
        "contract_type": kind,
        "amount": amount,
        "tax_basis": "HT",
        "currency": "EUR",
        "scope": "ordinary_whole_need",
        "trigger": "consultation_started",
        "trigger_date": when,
        **changes,
    }


@pytest.mark.parametrize(
    "when,amount,kind,threshold,met",
    [
        ("2026-03-20", "50000", "supplies", "40000", False),
        ("2026-04-01", "50000", "supplies", "60000", True),
        ("2026-04-01", "59999.99", "services", "60000", True),
        ("2026-04-01", "60000", "supplies", "60000", False),
        ("2026-01-01", "99999.99", "works", "100000", True),
        ("2026-01-01", "100000", "works", "100000", False),
    ],
)
def test_dispense_date_and_exact_boundaries(when, amount, kind, threshold, met):
    result = evaluate("procurement.dispense", facts(amount, when, kind), date.fromisoformat(when))
    assert result["threshold_eur_ht"] == threshold
    assert result["amount_condition_met"] is met
    assert result["legal_validity"] == "not_assessed" and result["remaining_checks"]


@pytest.mark.parametrize(
    "amount,expected", [("215999.99", False), ("216000", True), ("216000.01", True)]
)
def test_formal_threshold_is_inclusive(amount, expected):
    result = evaluate("procurement.formal_threshold", facts(amount), date(2026, 4, 1))
    assert result["amount_condition_met"] is expected


@pytest.mark.parametrize(
    "changes,status",
    [
        ({"buyer_type": "contracting_entity"}, "not_covered"),
        ({"scope": "small_lot"}, "not_covered"),
        ({"contract_type": "concession"}, "not_covered"),
        ({"tax_basis": "TTC"}, "unknown"),
        ({"currency": "USD"}, "unknown"),
        ({"trigger": "note_written"}, "unknown"),
    ],
)
def test_no_silent_transposition(changes, status):
    assert evaluate("procurement.dispense", facts(**changes), date(2026, 4, 1))["status"] == status


def test_different_analysis_date_cannot_change_procedural_rule():
    result = evaluate("procurement.dispense", facts(when="2026-03-20"), date(2026, 9, 15))
    assert result["status"] == "unknown" and "trigger" in result["reason"]


def test_missing_and_out_of_coverage_dates():
    assert evaluate("procurement.dispense", {}, date(2026, 4, 1))["status"] == "unknown"
    for when in ["2025-12-31", "2027-01-01"]:
        assert (
            evaluate("procurement.dispense", facts(when=when), date.fromisoformat(when))["status"]
            == "not_covered"
        )


@pytest.mark.parametrize("amount", [True, 50000.1, "NaN", "Infinity", "-1", "texte"])
def test_amount_rejects_ambiguous_or_invalid_values(amount):
    with pytest.raises(SourceError):
        evaluate("procurement.dispense", facts(amount=amount), date(2026, 4, 1))


def test_no_universal_litigation_deadline():
    with pytest.raises(SourceError) as exc:
        evaluate("contentieux.deux_mois", {}, date(2026, 9, 15))
    assert exc.value.problem.code == "unsupported_rule"
