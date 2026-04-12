"""Tests for the LangGraph agent pipeline."""
import pytest
from src.pipeline import (
    AgentState,
    router_node,
    summarizer_node,
    classifier_node,
    impact_ranker_node,
    drafter_node,
    aggregator_node,
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
        errors=[],
        token_usage={},
        current_step="init",
    )


@pytest.mark.asyncio
async def test_router_node_sets_step(sample_state):
    result = await router_node(sample_state)
    assert result["current_step"] == "routing"


@pytest.mark.asyncio
async def test_summarizer_node_sets_step(sample_state):
    result = await summarizer_node(sample_state)
    assert result["current_step"] == "summarizing"


@pytest.mark.asyncio
async def test_classifier_node_sets_step(sample_state):
    result = await classifier_node(sample_state)
    assert result["current_step"] == "classifying"


@pytest.mark.asyncio
async def test_impact_ranker_sets_step(sample_state):
    result = await impact_ranker_node(sample_state)
    assert result["current_step"] == "ranking_impact"


@pytest.mark.asyncio
async def test_drafter_sets_step(sample_state):
    result = await drafter_node(sample_state)
    assert result["current_step"] == "drafting"


@pytest.mark.asyncio
async def test_aggregator_sets_step(sample_state):
    result = await aggregator_node(sample_state)
    assert result["current_step"] == "aggregating"


def test_summarizer_prompt_has_content_placeholder():
    assert "{content}" in SUMMARIZER_PROMPT


def test_classifier_prompt_has_required_placeholders():
    assert "{summary}" in CLASSIFIER_PROMPT
    assert "{key_changes}" in CLASSIFIER_PROMPT


def test_impact_ranker_prompt_has_required_placeholders():
    assert "{summary}" in IMPACT_RANKER_PROMPT
    assert "{classification}" in IMPACT_RANKER_PROMPT


def test_drafter_prompt_has_required_placeholders():
    assert "{audience}" in DRAFTER_PROMPT
    assert "{summary}" in DRAFTER_PROMPT
    assert "{key_changes}" in DRAFTER_PROMPT


def test_agent_state_structure():
    state = AgentState(
        document_id="test",
        raw_content="test content",
        metadata={},
        summary=None,
        key_changes=None,
        classification=None,
        impact_scores=None,
        draft_response=None,
        errors=[],
        token_usage={},
        current_step="init",
    )
    assert state["document_id"] == "test"
    assert state["errors"] == []
