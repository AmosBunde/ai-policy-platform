"""LangGraph multi-agent pipeline for regulatory document analysis."""
import json
import logging
import re
from typing import TypedDict, Optional

from shared.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AgentState(TypedDict):
    """State shared across all nodes in the LangGraph pipeline."""
    document_id: str
    raw_content: str
    metadata: dict
    summary: Optional[str]
    key_changes: Optional[list]
    classification: Optional[list]
    impact_scores: Optional[list]
    draft_response: Optional[str]
    affected_entities: Optional[list]
    effective_dates: Optional[list]
    urgency_level: str
    confidence_score: float
    errors: list
    token_usage: dict
    current_step: str


# ── Prompt Templates ───────────────────────────────────────

SUMMARIZER_PROMPT = """You are a regulatory policy analyst. Analyze the following regulatory document and extract:

1. **Executive Summary** (2-3 paragraphs)
2. **Key Changes** (bullet list with affected parties and effective dates)
3. **Affected Entities** (organizations, sectors, or populations impacted)
4. **Effective Dates** (all dates mentioned)

Document:
{content}

Respond in JSON format with keys: summary, key_changes, affected_entities, effective_dates
"""

CLASSIFIER_PROMPT = """Classify this regulatory document into one or more domains.

Available domains:
- privacy: Data protection, GDPR, personal information
- safety: AI safety, risk management, testing requirements
- intellectual_property: Copyright, patents, trade secrets for AI
- antitrust: Competition, market dominance, merger review
- export_control: Cross-border data, technology transfer
- sector_specific: Healthcare, finance, education, defense
- transparency: Disclosure, explainability, algorithmic auditing
- liability: Legal responsibility, insurance, redress

Document Summary:
{summary}

Key Changes:
{key_changes}

Respond in JSON: [{{"domain": "...", "confidence": 0.0-1.0, "sub_categories": [...]}}]
"""

IMPACT_RANKER_PROMPT = """Score the regulatory impact of this document on a 1-10 scale.

Regions to score: EU, US-Federal, US-State, UK, Canada, APAC, LatAm, Africa, Middle East
Product categories: SaaS, Consumer AI, Enterprise AI, Healthcare AI, Financial AI, Autonomous Systems, GenAI

Document Summary:
{summary}

Classification:
{classification}

For each relevant region x product combination, provide:
- score (1-10, where 10 = highest impact)
- justification (1 sentence)

Respond in JSON: [{{"region": "...", "product_category": "...", "score": N, "justification": "..."}}]
"""

DRAFTER_PROMPT = """Draft a compliance response for the following regulatory change.

Target audience: {audience}

Summary:
{summary}

Key Changes:
{key_changes}

Impact Assessment:
{impact_scores}

Generate a professional compliance response that includes:
1. Acknowledgment of the regulatory change
2. Assessment of applicability to the organization
3. Recommended actions with timelines
4. Resource requirements estimate
"""


# ── Validation Helpers ────────────────────────────────────

def _validate_summary_output(data: dict) -> dict:
    """Validate LLM output matches expected summary schema."""
    if not isinstance(data, dict):
        raise ValueError("Summary output must be a JSON object")
    if "summary" not in data or not isinstance(data["summary"], str):
        raise ValueError("Summary output must contain a 'summary' string")
    data.setdefault("key_changes", [])
    data.setdefault("affected_entities", [])
    data.setdefault("effective_dates", [])
    return data


def _validate_classification_output(data: list) -> list:
    """Validate classification output schema."""
    if not isinstance(data, list):
        raise ValueError("Classification output must be a JSON array")
    validated = []
    for item in data:
        if not isinstance(item, dict) or "domain" not in item:
            continue
        conf = item.get("confidence", 0.5)
        if not isinstance(conf, (int, float)) or conf < 0 or conf > 1:
            conf = 0.5
        validated.append({
            "domain": str(item["domain"]),
            "confidence": float(conf),
            "sub_categories": item.get("sub_categories", []),
        })
    return validated


def _validate_impact_output(data: list) -> list:
    """Validate impact scores: enforce score 1-10 range."""
    if not isinstance(data, list):
        raise ValueError("Impact output must be a JSON array")
    validated = []
    for item in data:
        if not isinstance(item, dict):
            continue
        score = item.get("score", 5)
        if not isinstance(score, (int, float)):
            score = 5
        score = max(1, min(10, int(score)))
        validated.append({
            "region": str(item.get("region", "unknown")),
            "product_category": str(item.get("product_category", "unknown")),
            "score": score,
            "justification": str(item.get("justification", "")),
        })
    return validated


def _calculate_urgency(impact_scores: list) -> str:
    """Derive urgency level from max impact score."""
    if not impact_scores:
        return "normal"
    max_score = max(s.get("score", 0) for s in impact_scores)
    if max_score >= 8:
        return "critical"
    if max_score >= 6:
        return "high"
    if max_score >= 4:
        return "normal"
    return "low"


# ── Node Functions ─────────────────────────────────────────

async def router_node(state: AgentState) -> AgentState:
    """Route document: detect language, set processing flags."""
    state["current_step"] = "routing"
    metadata = state.get("metadata", {})
    content = state.get("raw_content", "")

    # Detect language from common words
    en_words = len(re.findall(r"\b(the|and|of|to|in|is|that|for)\b", content, re.I))
    metadata["detected_language"] = "en" if en_words > 2 else "unknown"
    metadata["content_length"] = len(content)
    state["metadata"] = metadata
    return state


async def summarizer_node(state: AgentState) -> AgentState:
    """Extract summary and key changes via LLM."""
    state["current_step"] = "summarizing"

    from src.llm_client import call_llm, parse_json_response
    from src.chunker import chunk_document

    content = state["raw_content"]
    chunks = chunk_document(content)

    # Summarize first chunk (or whole document if small)
    chunk_text = chunks[0].text if chunks else content
    prompt = SUMMARIZER_PROMPT.format(content=chunk_text)

    try:
        result = await call_llm(prompt)
        data = parse_json_response(result["content"])
        validated = _validate_summary_output(data)

        state["summary"] = validated["summary"]
        state["key_changes"] = validated["key_changes"]
        state["affected_entities"] = validated.get("affected_entities", [])
        state["effective_dates"] = validated.get("effective_dates", [])
        state["token_usage"]["summarizer"] = {
            "input": result["input_tokens"],
            "output": result["output_tokens"],
            "cost": result["cost"],
        }
    except Exception as exc:
        state["errors"].append(f"Summarizer failed: {exc}")
        state["summary"] = ""
        state["key_changes"] = []

    return state


async def classifier_node(state: AgentState) -> AgentState:
    """Multi-label classification with confidence scores."""
    state["current_step"] = "classifying"

    from src.llm_client import call_llm, parse_json_response

    prompt = CLASSIFIER_PROMPT.format(
        summary=state.get("summary", ""),
        key_changes=json.dumps(state.get("key_changes", [])),
    )

    try:
        result = await call_llm(prompt)
        data = parse_json_response(result["content"])
        state["classification"] = _validate_classification_output(data)
        state["token_usage"]["classifier"] = {
            "input": result["input_tokens"],
            "output": result["output_tokens"],
            "cost": result["cost"],
        }
    except Exception as exc:
        state["errors"].append(f"Classifier failed: {exc}")
        state["classification"] = []

    return state


async def impact_ranker_node(state: AgentState) -> AgentState:
    """Score impact across region x product matrix."""
    state["current_step"] = "ranking_impact"

    from src.llm_client import call_llm, parse_json_response

    prompt = IMPACT_RANKER_PROMPT.format(
        summary=state.get("summary", ""),
        classification=json.dumps(state.get("classification", [])),
    )

    try:
        result = await call_llm(prompt)
        data = parse_json_response(result["content"])
        state["impact_scores"] = _validate_impact_output(data)
        state["token_usage"]["impact_ranker"] = {
            "input": result["input_tokens"],
            "output": result["output_tokens"],
            "cost": result["cost"],
        }
    except Exception as exc:
        state["errors"].append(f"Impact ranker failed: {exc}")
        state["impact_scores"] = []

    return state


async def drafter_node(state: AgentState) -> AgentState:
    """Generate compliance response draft."""
    state["current_step"] = "drafting"

    from src.llm_client import call_llm

    prompt = DRAFTER_PROMPT.format(
        audience="legal_review",
        summary=state.get("summary", ""),
        key_changes=json.dumps(state.get("key_changes", [])),
        impact_scores=json.dumps(state.get("impact_scores", [])),
    )

    try:
        result = await call_llm(prompt)
        state["draft_response"] = result["content"]
        state["token_usage"]["drafter"] = {
            "input": result["input_tokens"],
            "output": result["output_tokens"],
            "cost": result["cost"],
        }
    except Exception as exc:
        state["errors"].append(f"Drafter failed: {exc}")
        state["draft_response"] = None

    return state


def should_skip_drafter(state: AgentState) -> str:
    """Conditional edge: skip drafter for low-impact documents (max score < 3)."""
    scores = state.get("impact_scores", [])
    if not scores:
        return "aggregator"
    max_score = max(s.get("score", 0) for s in scores)
    if max_score < 3:
        return "aggregator"
    return "drafter"


async def error_handler_node(state: AgentState) -> AgentState:
    """Handle errors from any node gracefully."""
    state["current_step"] = "error_handling"
    logger.error("Pipeline errors for %s: %s", state["document_id"], state["errors"])
    return state


async def aggregator_node(state: AgentState) -> AgentState:
    """Merge all outputs, validate completeness, calculate confidence."""
    state["current_step"] = "aggregating"

    # Calculate overall confidence based on completeness
    completeness = 0
    if state.get("summary"):
        completeness += 0.3
    if state.get("classification"):
        completeness += 0.2
    if state.get("impact_scores"):
        completeness += 0.3
    if state.get("draft_response"):
        completeness += 0.2
    if state.get("errors"):
        completeness *= 0.7  # Penalize errors

    state["confidence_score"] = round(completeness, 2)
    state["urgency_level"] = _calculate_urgency(state.get("impact_scores", []))

    # Total token usage
    total_cost = sum(
        v.get("cost", 0) for v in state.get("token_usage", {}).values()
        if isinstance(v, dict)
    )
    state["token_usage"]["total_cost"] = total_cost

    return state


# ── Graph Builder ──────────────────────────────────────────

def build_agent_graph():
    """Build the LangGraph StateGraph with conditional routing and error handling."""
    from langgraph.graph import END, StateGraph

    graph = StateGraph(AgentState)

    graph.add_node("router", router_node)
    graph.add_node("summarizer", summarizer_node)
    graph.add_node("classifier", classifier_node)
    graph.add_node("impact_ranker", impact_ranker_node)
    graph.add_node("drafter", drafter_node)
    graph.add_node("aggregator", aggregator_node)
    graph.add_node("error_handler", error_handler_node)

    graph.set_entry_point("router")
    graph.add_edge("router", "summarizer")
    graph.add_edge("summarizer", "classifier")
    graph.add_edge("classifier", "impact_ranker")

    # Conditional: skip drafter for low-impact docs
    graph.add_conditional_edges(
        "impact_ranker",
        should_skip_drafter,
        {"drafter": "drafter", "aggregator": "aggregator"},
    )
    graph.add_edge("drafter", "aggregator")
    graph.add_edge("error_handler", "aggregator")
    graph.add_edge("aggregator", END)

    return graph.compile()


# ── Pipeline Runner ────────────────────────────────────────

async def run_pipeline(document_id: str, content: str, metadata: dict) -> dict:
    """Execute the full pipeline and return enrichment data."""
    initial_state: AgentState = {
        "document_id": document_id,
        "raw_content": content,
        "metadata": metadata,
        "summary": None,
        "key_changes": None,
        "classification": None,
        "impact_scores": None,
        "draft_response": None,
        "affected_entities": None,
        "effective_dates": None,
        "urgency_level": "normal",
        "confidence_score": 0.0,
        "errors": [],
        "token_usage": {},
        "current_step": "init",
    }

    graph = build_agent_graph()
    final_state = await graph.ainvoke(initial_state)

    return {
        "summary": final_state.get("summary"),
        "key_changes": final_state.get("key_changes", []),
        "classification": final_state.get("classification", []),
        "impact_scores": final_state.get("impact_scores", []),
        "draft_response": final_state.get("draft_response"),
        "affected_entities": final_state.get("affected_entities", []),
        "effective_dates": final_state.get("effective_dates", []),
        "urgency_level": final_state.get("urgency_level", "normal"),
        "confidence_score": final_state.get("confidence_score", 0.0),
        "token_usage": final_state.get("token_usage", {}),
    }
