"""Tests for rule engine: all operators, edge cases, type validation, no code injection."""
import pytest
from src.rule_engine import evaluate_condition, evaluate_rule, flatten_enrichment


class TestEquals:
    def test_string_equals(self):
        assert evaluate_condition({"field": "jurisdiction", "operator": "equals", "value": "EU"}, {"jurisdiction": "EU"})

    def test_case_insensitive(self):
        assert evaluate_condition({"field": "jurisdiction", "operator": "equals", "value": "eu"}, {"jurisdiction": "EU"})

    def test_not_equal(self):
        assert not evaluate_condition({"field": "jurisdiction", "operator": "equals", "value": "US"}, {"jurisdiction": "EU"})


class TestContains:
    def test_string_contains(self):
        assert evaluate_condition({"field": "keyword", "operator": "contains", "value": "privacy"}, {"keyword": "data privacy regulation"})

    def test_not_contains(self):
        assert not evaluate_condition({"field": "keyword", "operator": "contains", "value": "crypto"}, {"keyword": "data privacy"})

    def test_case_insensitive(self):
        assert evaluate_condition({"field": "keyword", "operator": "contains", "value": "GDPR"}, {"keyword": "gdpr regulation"})


class TestGte:
    def test_gte_true(self):
        assert evaluate_condition({"field": "score", "operator": "gte", "value": 5}, {"score": 8})

    def test_gte_equal(self):
        assert evaluate_condition({"field": "score", "operator": "gte", "value": 5}, {"score": 5})

    def test_gte_false(self):
        assert not evaluate_condition({"field": "score", "operator": "gte", "value": 5}, {"score": 3})


class TestLte:
    def test_lte_true(self):
        assert evaluate_condition({"field": "score", "operator": "lte", "value": 5}, {"score": 3})

    def test_lte_equal(self):
        assert evaluate_condition({"field": "score", "operator": "lte", "value": 5}, {"score": 5})

    def test_lte_false(self):
        assert not evaluate_condition({"field": "score", "operator": "lte", "value": 5}, {"score": 8})


class TestIn:
    def test_in_list(self):
        assert evaluate_condition({"field": "jurisdiction", "operator": "in", "value": ["EU", "UK", "US"]}, {"jurisdiction": "EU"})

    def test_not_in_list(self):
        assert not evaluate_condition({"field": "jurisdiction", "operator": "in", "value": ["UK", "US"]}, {"jurisdiction": "EU"})


class TestNotIn:
    def test_not_in(self):
        assert evaluate_condition({"field": "jurisdiction", "operator": "not_in", "value": ["UK", "US"]}, {"jurisdiction": "EU"})

    def test_in_rejects(self):
        assert not evaluate_condition({"field": "jurisdiction", "operator": "not_in", "value": ["EU", "UK"]}, {"jurisdiction": "EU"})


class TestEdgeCases:
    def test_missing_field_returns_false(self):
        assert not evaluate_condition({"field": "jurisdiction", "operator": "equals", "value": "EU"}, {})

    def test_unknown_operator_returns_false(self):
        assert not evaluate_condition({"field": "jurisdiction", "operator": "regex", "value": ".*"}, {"jurisdiction": "EU"})

    def test_unknown_field_returns_false(self):
        assert not evaluate_condition({"field": "unknown_field", "operator": "equals", "value": "test"}, {"unknown_field": "test"})

    def test_none_value_returns_false(self):
        assert not evaluate_condition({"field": "jurisdiction", "operator": "equals", "value": "EU"}, {"jurisdiction": None})


class TestNoCodeInjection:
    def test_eval_in_value_is_just_a_string(self):
        """Ensure eval() expressions in values are treated as plain strings."""
        result = evaluate_condition(
            {"field": "keyword", "operator": "contains", "value": "__import__('os').system('rm -rf /')"},
            {"keyword": "safe content"},
        )
        assert result is False

    def test_exec_in_operator_rejected(self):
        assert not evaluate_condition(
            {"field": "keyword", "operator": "exec", "value": "print('hacked')"},
            {"keyword": "test"},
        )


class TestEvaluateRule:
    def test_all_conditions_match(self):
        conditions = [
            {"field": "jurisdiction", "operator": "equals", "value": "EU"},
            {"field": "score", "operator": "gte", "value": 7},
        ]
        data = {"jurisdiction": "EU", "score": 8}
        assert evaluate_rule(conditions, data)

    def test_one_condition_fails(self):
        conditions = [
            {"field": "jurisdiction", "operator": "equals", "value": "EU"},
            {"field": "score", "operator": "gte", "value": 9},
        ]
        data = {"jurisdiction": "EU", "score": 5}
        assert not evaluate_rule(conditions, data)

    def test_empty_conditions_returns_false(self):
        assert not evaluate_rule([], {"jurisdiction": "EU"})


class TestFlattenEnrichment:
    def test_flattens_basic(self):
        enrichment = {
            "urgency_level": "high",
            "confidence_score": 0.85,
            "classification": [{"domain": "safety", "confidence": 0.9}],
            "impact_scores": [{"score": 8}, {"score": 3}],
            "summary": "AI regulation update",
        }
        flat = flatten_enrichment(enrichment)
        assert flat["urgency_level"] == "high"
        assert flat["confidence"] == 0.85
        assert flat["domain"] == "safety"
        assert flat["score"] == 8
        assert "AI regulation" in flat["keyword"]

    def test_handles_empty_enrichment(self):
        flat = flatten_enrichment({})
        assert flat["urgency_level"] == "normal"
        assert flat["confidence"] == 0.0
