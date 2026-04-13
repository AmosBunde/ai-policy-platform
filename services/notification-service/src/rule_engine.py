"""Watch rule evaluation engine — explicit operator mapping only (no eval/exec)."""
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Allowed condition fields and their expected value types
ALLOWED_FIELDS = {
    "jurisdiction": str,
    "category": str,
    "urgency_level": str,
    "document_type": str,
    "keyword": str,
    "domain": str,
    "score": (int, float),
    "confidence": (int, float),
}


def _validate_condition(field: str, operator: str, value: Any) -> bool:
    """Validate that field, operator, and value are well-typed."""
    if field not in ALLOWED_FIELDS:
        logger.warning("Unknown condition field: %s", field)
        return False

    expected_type = ALLOWED_FIELDS[field]
    if isinstance(expected_type, tuple):
        if not isinstance(value, expected_type):
            return False
    else:
        if not isinstance(value, expected_type):
            return False

    return True


def _op_equals(actual: Any, expected: Any) -> bool:
    if isinstance(actual, str) and isinstance(expected, str):
        return actual.lower() == expected.lower()
    return actual == expected


def _op_contains(actual: Any, expected: Any) -> bool:
    if isinstance(actual, str) and isinstance(expected, str):
        return expected.lower() in actual.lower()
    if isinstance(actual, list):
        return expected in actual
    return False


def _op_gte(actual: Any, expected: Any) -> bool:
    try:
        return float(actual) >= float(expected)
    except (TypeError, ValueError):
        return False


def _op_lte(actual: Any, expected: Any) -> bool:
    try:
        return float(actual) <= float(expected)
    except (TypeError, ValueError):
        return False


def _op_in(actual: Any, expected: Any) -> bool:
    if isinstance(expected, list):
        if isinstance(actual, str):
            return actual.lower() in [str(v).lower() for v in expected]
        return actual in expected
    return False


def _op_not_in(actual: Any, expected: Any) -> bool:
    return not _op_in(actual, expected)


# Explicit operator mapping — NEVER use eval/exec
_OPERATORS = {
    "equals": _op_equals,
    "contains": _op_contains,
    "gte": _op_gte,
    "lte": _op_lte,
    "in": _op_in,
    "not_in": _op_not_in,
}


def evaluate_condition(condition: dict, enrichment_data: dict) -> bool:
    """Evaluate a single watch rule condition against enrichment data.

    condition: {"field": "...", "operator": "...", "value": ...}
    enrichment_data: flat dict of enrichment fields
    """
    field = condition.get("field", "")
    operator = condition.get("operator", "")
    value = condition.get("value")

    if field not in ALLOWED_FIELDS:
        logger.warning("Unknown field: %s", field)
        return False

    if operator not in _OPERATORS:
        logger.warning("Unknown operator: %s", operator)
        return False

    actual_value = enrichment_data.get(field)
    if actual_value is None:
        return False

    op_func = _OPERATORS[operator]
    return op_func(actual_value, value)


def evaluate_rule(conditions: list[dict], enrichment_data: dict) -> bool:
    """Evaluate all conditions in a watch rule (AND logic).

    Returns True if ALL conditions match.
    """
    if not conditions:
        return False

    for condition in conditions:
        if not evaluate_condition(condition, enrichment_data):
            return False

    return True


def flatten_enrichment(enrichment: dict) -> dict:
    """Flatten enrichment data for rule evaluation."""
    flat = {}
    flat["urgency_level"] = enrichment.get("urgency_level", "normal")
    flat["confidence"] = enrichment.get("confidence_score", 0.0)

    # Flatten classification domains
    for cls in enrichment.get("classification", []):
        flat["domain"] = cls.get("domain", "")
        break  # Use first classification for simple matching

    # Max impact score
    scores = enrichment.get("impact_scores", [])
    if scores:
        flat["score"] = max(s.get("score", 0) for s in scores)

    # Summary as keyword source
    flat["keyword"] = enrichment.get("summary", "")

    return flat
