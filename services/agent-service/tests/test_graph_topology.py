"""Smoke tests for the compiled LangGraph pipeline (langgraph 1.x)."""

from src.pipeline import build_agent_graph

EXPECTED_NODES = {
    "router",
    "summarizer",
    "classifier",
    "impact_ranker",
    "drafter",
    "aggregator",
    "error_handler",
}


class TestGraphTopology:
    def test_graph_compiles(self):
        compiled = build_agent_graph()
        assert compiled is not None

    def test_all_agent_nodes_present(self):
        graph = build_agent_graph().get_graph()
        node_names = set(graph.nodes.keys()) - {"__start__", "__end__"}
        assert node_names == EXPECTED_NODES

    def test_entry_point_is_router(self):
        graph = build_agent_graph().get_graph()
        entry_targets = {e.target for e in graph.edges if e.source == "__start__"}
        assert entry_targets == {"router"}

    def test_impact_ranker_branches_conditionally(self):
        """Low-impact documents skip the drafter and go straight to aggregation."""
        graph = build_agent_graph().get_graph()
        targets = {e.target for e in graph.edges if e.source == "impact_ranker"}
        assert targets == {"drafter", "aggregator"}

    def test_aggregator_terminates(self):
        graph = build_agent_graph().get_graph()
        targets = {e.target for e in graph.edges if e.source == "aggregator"}
        assert targets == {"__end__"}
