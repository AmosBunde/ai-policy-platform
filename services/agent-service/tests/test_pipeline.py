"""Tests for the LangGraph agent pipeline — all with mocked OpenAI."""
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.pipeline import (
    AgentState,
    router_node,
    summarizer_node,
    classifier_node,
    impact_ranker_node,
    drafter_node,
    aggregator_node,
    should_skip_drafter,
    error_handler_node,
    _validate_summary_output,
    _validate_classification_output,
    _validate_impact_output,
    _calculate_urgency,
    SUMMARIZER_PROMPT,
    CLASSIFIER_PROMPT,
    IMPACT_RANKER_PROMPT,
    DRAFTER_PROMPT,
)


@pytest.fixture
def sample_state() -> AgentState:
    return AgentState(
        document_id="test-doc-001",
        raw_content="The European Union has adopted new regulations requiring all AI systems "
                     "used in hiring decisions to undergo mandatory bias audits before deployment. "
                     "Companies must comply by January 1, 2027.",
        metadata={"source": "eu_official", "jurisdiction": "EU"},
        summary=None,
        key_changes=None,
        classification=None,
        impact_scores=None,
        draft_response=None,
        affected_entities=None,
        effective_dates=None,
        urgency_level="normal",
        confidence_score=0.0,
        errors=[],
        token_usage={},
        current_step="init",
    )


class TestRouterNode:
    @pytest.mark.asyncio
    async def test_sets_step(self, sample_state):
        result = await router_node(sample_state)
        assert result["current_step"] == "routing"

    @pytest.mark.asyncio
    async def test_detects_language(self, sample_state):
        result = await router_node(sample_state)
        assert result["metadata"]["detected_language"] == "en"

    @pytest.mark.asyncio
    async def test_sets_content_length(self, sample_state):
        result = await router_node(sample_state)
        assert result["metadata"]["content_length"] > 0


class TestSummarizerNode:
    @pytest.mark.asyncio
    async def test_summarizer_success(self, sample_state):
        mock_llm_result = {
            "content": json.dumps({
                "summary": "The EU requires AI bias audits.",
                "key_changes": [{"change": "Mandatory bias audits"}],
                "affected_entities": ["AI companies"],
                "effective_dates": ["2027-01-01"],
            }),
            "input_tokens": 500,
            "output_tokens": 200,
            "cost": 0.005,
        }
        with patch("src.llm_client.call_llm", new_callable=AsyncMock, return_value=mock_llm_result):
            result = await summarizer_node(sample_state)
            assert result["summary"] == "The EU requires AI bias audits."
            assert len(result["key_changes"]) == 1
            assert "summarizer" in result["token_usage"]

    @pytest.mark.asyncio
    async def test_summarizer_handles_llm_failure(self, sample_state):
        with patch("src.llm_client.call_llm", new_callable=AsyncMock, side_effect=RuntimeError("LLM down")):
            result = await summarizer_node(sample_state)
            assert result["summary"] == ""
            assert any("Summarizer failed" in e for e in result["errors"])


class TestClassifierNode:
    @pytest.mark.asyncio
    async def test_classifier_success(self, sample_state):
        sample_state["summary"] = "AI regulation summary"
        sample_state["key_changes"] = []
        mock_result = {
            "content": json.dumps([
                {"domain": "safety", "confidence": 0.95, "sub_categories": ["bias"]},
                {"domain": "transparency", "confidence": 0.7, "sub_categories": []},
            ]),
            "input_tokens": 300,
            "output_tokens": 100,
            "cost": 0.003,
        }
        with patch("src.llm_client.call_llm", new_callable=AsyncMock, return_value=mock_result):
            result = await classifier_node(sample_state)
            assert len(result["classification"]) == 2
            assert result["classification"][0]["domain"] == "safety"


class TestImpactRankerNode:
    @pytest.mark.asyncio
    async def test_impact_ranker_success(self, sample_state):
        sample_state["summary"] = "AI regulation"
        sample_state["classification"] = [{"domain": "safety", "confidence": 0.9}]
        mock_result = {
            "content": json.dumps([
                {"region": "EU", "product_category": "Enterprise AI", "score": 9, "justification": "Direct regulation"},
                {"region": "US-Federal", "product_category": "SaaS", "score": 3, "justification": "Indirect impact"},
            ]),
            "input_tokens": 400,
            "output_tokens": 150,
            "cost": 0.004,
        }
        with patch("src.llm_client.call_llm", new_callable=AsyncMock, return_value=mock_result):
            result = await impact_ranker_node(sample_state)
            assert len(result["impact_scores"]) == 2
            assert result["impact_scores"][0]["score"] == 9

    @pytest.mark.asyncio
    async def test_impact_ranker_clamps_scores(self, sample_state):
        sample_state["summary"] = "test"
        sample_state["classification"] = []
        mock_result = {
            "content": json.dumps([
                {"region": "EU", "product_category": "SaaS", "score": 15, "justification": "Over"},
                {"region": "UK", "product_category": "SaaS", "score": -2, "justification": "Under"},
            ]),
            "input_tokens": 100,
            "output_tokens": 50,
            "cost": 0.001,
        }
        with patch("src.llm_client.call_llm", new_callable=AsyncMock, return_value=mock_result):
            result = await impact_ranker_node(sample_state)
            assert result["impact_scores"][0]["score"] == 10  # Clamped to max
            assert result["impact_scores"][1]["score"] == 1   # Clamped to min


class TestDrafterNode:
    @pytest.mark.asyncio
    async def test_drafter_success(self, sample_state):
        sample_state["summary"] = "AI regulation requires audits."
        sample_state["key_changes"] = []
        sample_state["impact_scores"] = []
        mock_result = {
            "content": "We acknowledge the new regulation and recommend...",
            "input_tokens": 600,
            "output_tokens": 300,
            "cost": 0.007,
        }
        with patch("src.llm_client.call_llm", new_callable=AsyncMock, return_value=mock_result):
            result = await drafter_node(sample_state)
            assert result["draft_response"] is not None
            assert "acknowledge" in result["draft_response"]


class TestConditionalRouting:
    def test_skip_drafter_low_impact(self):
        state = {"impact_scores": [{"score": 2}, {"score": 1}]}
        assert should_skip_drafter(state) == "aggregator"

    def test_proceed_to_drafter_high_impact(self):
        state = {"impact_scores": [{"score": 8}, {"score": 2}]}
        assert should_skip_drafter(state) == "drafter"

    def test_skip_drafter_empty_scores(self):
        state = {"impact_scores": []}
        assert should_skip_drafter(state) == "aggregator"

    def test_skip_drafter_no_scores(self):
        state = {}
        assert should_skip_drafter(state) == "aggregator"


class TestAggregatorNode:
    @pytest.mark.asyncio
    async def test_aggregator_full_completeness(self, sample_state):
        sample_state["summary"] = "Summary"
        sample_state["classification"] = [{"domain": "safety"}]
        sample_state["impact_scores"] = [{"score": 8}]
        sample_state["draft_response"] = "Draft"
        sample_state["token_usage"] = {"summarizer": {"cost": 0.01}, "classifier": {"cost": 0.005}}

        result = await aggregator_node(sample_state)
        assert result["confidence_score"] == 1.0
        assert result["urgency_level"] == "critical"

    @pytest.mark.asyncio
    async def test_aggregator_partial_completeness(self, sample_state):
        sample_state["summary"] = "Summary"
        result = await aggregator_node(sample_state)
        assert result["confidence_score"] < 1.0

    @pytest.mark.asyncio
    async def test_aggregator_penalizes_errors(self, sample_state):
        sample_state["summary"] = "Summary"
        sample_state["errors"] = ["Some error"]
        result = await aggregator_node(sample_state)
        assert result["confidence_score"] < 0.3


class TestUrgencyCalculation:
    def test_critical(self):
        assert _calculate_urgency([{"score": 9}]) == "critical"

    def test_high(self):
        assert _calculate_urgency([{"score": 7}]) == "high"

    def test_normal(self):
        assert _calculate_urgency([{"score": 5}]) == "normal"

    def test_low(self):
        assert _calculate_urgency([{"score": 2}]) == "low"

    def test_empty(self):
        assert _calculate_urgency([]) == "normal"


class TestValidation:
    def test_validate_summary_valid(self):
        data = {"summary": "Test summary"}
        result = _validate_summary_output(data)
        assert result["summary"] == "Test summary"

    def test_validate_summary_rejects_non_dict(self):
        with pytest.raises(ValueError):
            _validate_summary_output("not a dict")

    def test_validate_summary_rejects_missing_summary(self):
        with pytest.raises(ValueError):
            _validate_summary_output({"key_changes": []})

    def test_validate_classification_clamps_confidence(self):
        data = [{"domain": "safety", "confidence": 1.5}]
        result = _validate_classification_output(data)
        assert result[0]["confidence"] == 0.5  # Reset to default

    def test_validate_impact_clamps_score(self):
        data = [{"region": "EU", "product_category": "SaaS", "score": 15}]
        result = _validate_impact_output(data)
        assert result[0]["score"] == 10


class TestPromptTemplates:
    def test_summarizer_prompt_has_placeholder(self):
        assert "{content}" in SUMMARIZER_PROMPT

    def test_classifier_prompt_has_placeholders(self):
        assert "{summary}" in CLASSIFIER_PROMPT
        assert "{key_changes}" in CLASSIFIER_PROMPT

    def test_impact_ranker_prompt_has_placeholders(self):
        assert "{summary}" in IMPACT_RANKER_PROMPT
        assert "{classification}" in IMPACT_RANKER_PROMPT

    def test_drafter_prompt_has_placeholders(self):
        assert "{audience}" in DRAFTER_PROMPT
        assert "{summary}" in DRAFTER_PROMPT
