"""Deliberately bounded monetary tests; no universal legal decision or deadline calculator."""

import json
from datetime import date
from decimal import Decimal, InvalidOperation

from .models import SourceError
from .resources import data_path


def evaluate(rule_id: str, facts: dict, as_of_date: date):
    registry = json.loads((data_path("registry") / "rules.json").read_text())
    rule = registry["rules"].get(rule_id)
    if rule is None:
        raise SourceError("unsupported_rule", "Supported rules: " + ", ".join(registry["rules"]))
    required = {
        "buyer_type",
        "contract_type",
        "amount",
        "tax_basis",
        "currency",
        "scope",
        "trigger",
        "trigger_date",
    }
    missing = sorted(required - facts.keys())
    if missing:
        return {"status": "unknown", "missing_facts": missing, "legal_validity": "not_assessed"}
    if (
        facts["buyer_type"] != "other_contracting_authority"
        or facts["scope"] != "ordinary_whole_need"
    ):
        return {
            "status": "not_covered",
            "reason": "Qualify the buyer, whole need and special regimes before selecting a rule",
        }
    if facts["contract_type"] not in {"supplies", "services", "works"}:
        return {"status": "not_covered", "reason": "Contract type outside this rule"}
    if facts["tax_basis"] != "HT" or facts["currency"] != "EUR":
        return {
            "status": "unknown",
            "reason": "A justified amount in EUR excluding tax is required; no implicit conversion",
        }
    if facts["trigger"] not in {"consultation_started", "notice_sent"}:
        return {
            "status": "unknown",
            "reason": "Determine the procedural trigger specified by the text",
        }
    try:
        trigger_date = date.fromisoformat(facts["trigger_date"])
    except (ValueError, TypeError):
        raise SourceError("invalid_input", "trigger_date must use YYYY-MM-DD") from None
    if trigger_date != as_of_date:
        return {
            "status": "unknown",
            "reason": "as_of_date must be the procedural trigger date, not today's analysis date",
            "trigger_date": trigger_date.isoformat(),
        }
    if isinstance(facts["amount"], (bool, float)):
        raise SourceError(
            "invalid_input", "Pass the amount as a decimal string or integer, not float/bool"
        )
    try:
        amount = Decimal(str(facts["amount"]))
        if not amount.is_finite() or amount < 0:
            raise InvalidOperation
    except (InvalidOperation, ValueError):
        raise SourceError("invalid_input", "Amount must be finite and non-negative") from None
    version = next(
        (
            v
            for v in rule["versions"]
            if date.fromisoformat(v["from"]) <= as_of_date < date.fromisoformat(v["until"])
        ),
        None,
    )
    if version is None:
        return {"status": "not_covered", "reason": "Date outside the reviewed rule intervals"}
    threshold = Decimal(version[facts["contract_type"]])
    result = amount < threshold if rule["comparator"] == "lt" else amount >= threshold
    return {
        "status": "calculated",
        "rule_id": rule_id,
        "rule_version": version["from"],
        "reviewed_at": registry["reviewed_at"],
        "maturity": registry["status"],
        "as_of_date": as_of_date.isoformat(),
        "premises": facts,
        "threshold_eur_ht": str(threshold),
        "comparator": rule["comparator"],
        "amount_condition_met": result,
        "sources": rule["sources"],
        "remaining_checks": rule["remaining_checks"],
        "legal_validity": "not_assessed",
        "decision": "No procedure or purchase authorization is inferred from this numerical test",
        "freshness": "Static reviewed registry; revalidate sources for operational use",
    }
