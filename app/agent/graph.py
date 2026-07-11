"""
agent/graph.py
Supervisor agent: orchestrates discovery -> fetch -> target -> train -> report,
pausing for the user at dataset choice and (if needed) target confirmation.

  START -> search -> choose --(no datasets)--> END
                        |--(picked)--> fetch -> resolve_target -> train -> END

Deterministic control flow; the LLM is used only inside resolve_target (target
resolution for unlabeled sources). MemorySaver keeps each run by thread_id.
"""

from functools import lru_cache

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from agent import nodes
from agent.state import AgentState


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("search", nodes.search_node)
    g.add_node("choose", nodes.choose_node)
    g.add_node("fetch", nodes.fetch_node)
    g.add_node("resolve_target", nodes.resolve_target_node)
    g.add_node("train", nodes.train_node)

    g.add_edge(START, "search")
    g.add_edge("search", "choose")
    g.add_conditional_edges("choose", nodes.route_after_choose, {"fetch": "fetch", "end": END})
    g.add_edge("fetch", "resolve_target")
    g.add_edge("resolve_target", "train")
    g.add_edge("train", END)

    return g.compile(checkpointer=MemorySaver())


@lru_cache
def get_graph():
    return build_graph()
