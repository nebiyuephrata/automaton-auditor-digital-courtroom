from typing import Literal

from src.nodes.aggregator import EvidenceAggregator
from src.nodes.detectives import DocAnalyst, RepoInvestigator, VisionInspector
from src.nodes.judges import DefenseNode, ProsecutorNode, TechLeadNode
from src.nodes.justice import ChiefJusticeNode
from src.state import AgentState

try:
    from langgraph.graph import END, START, StateGraph
except Exception:  # pragma: no cover
    START = "__start__"
    END = "__end__"

    class StateGraph:  # type: ignore[override]
        def __init__(self, *args, **kwargs):
            self.nodes = {}

        def add_node(self, name, fn):
            self.nodes[name] = fn

        def add_edge(self, src, dst):
            return None

        def add_conditional_edges(self, src, router, mapping):
            return None

        def compile(self):
            return self


def route_after_aggregation(state: AgentState) -> Literal["proceed", "error"]:
    return "error" if state.get("errors") else "proceed"


def route_after_justice(state: AgentState) -> Literal["end", "error"]:
    return "error" if state.get("errors") else "end"


def error_handler(state: AgentState) -> AgentState:
    return {"errors": state.get("errors", []) + ["graph_routed_to_error_handler"]}


def create_graph():
    builder = StateGraph(AgentState)

    builder.add_node("repo_investigator", RepoInvestigator())
    builder.add_node("doc_analyst", DocAnalyst())
    builder.add_node("vision_inspector", VisionInspector())
    builder.add_node("evidence_aggregator", EvidenceAggregator())

    builder.add_node("prosecutor", ProsecutorNode())
    builder.add_node("defense", DefenseNode())
    builder.add_node("techlead", TechLeadNode())

    builder.add_node("chief_justice", ChiefJusticeNode())
    builder.add_node("error_handler", error_handler)

    builder.add_edge(START, "repo_investigator")
    builder.add_edge(START, "doc_analyst")
    builder.add_edge(START, "vision_inspector")

    builder.add_edge("repo_investigator", "evidence_aggregator")
    builder.add_edge("doc_analyst", "evidence_aggregator")
    builder.add_edge("vision_inspector", "evidence_aggregator")

    builder.add_conditional_edges(
        "evidence_aggregator",
        route_after_aggregation,
        {
            "proceed": "prosecutor",
            "error": "error_handler",
        },
    )

    builder.add_edge("evidence_aggregator", "defense")
    builder.add_edge("evidence_aggregator", "techlead")

    builder.add_edge("prosecutor", "chief_justice")
    builder.add_edge("defense", "chief_justice")
    builder.add_edge("techlead", "chief_justice")

    builder.add_conditional_edges(
        "chief_justice",
        route_after_justice,
        {
            "end": END,
            "error": "error_handler",
        },
    )
    builder.add_edge("error_handler", END)

    return builder.compile()
