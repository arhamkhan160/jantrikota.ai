"""
validation/graph.py
Wires the validation nodes into a stateful LangGraph with human-in-the-loop.

  START -> profile -> review -> gate --(conditional)--> ask_user -> apply -> profile (loop)
                                          |                          ^
                                          +--> apply -----------------+
                                          +--> END

MemorySaver checkpointer keeps each run's state in memory keyed by thread_id
(single-worker default). Swap for a durable checkpointer when running >1 worker.
"""

from functools import lru_cache

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from validation import nodes
from validation.state import ValidationState


def build_graph():
    g = StateGraph(ValidationState)
    g.add_node("profile", nodes.profile_node)
    g.add_node("review", nodes.review_node)
    g.add_node("gate", nodes.gate_node)
    g.add_node("ask_user", nodes.ask_user_node)
    g.add_node("apply", nodes.apply_node)

    g.add_edge(START, "profile")
    g.add_edge("profile", "review")
    g.add_edge("review", "gate")
    g.add_conditional_edges(
        "gate", nodes.route_after_gate,
        {"ask_user": "ask_user", "apply": "apply", "end": END},
    )
    g.add_edge("ask_user", "apply")
    g.add_edge("apply", "profile")

    return g.compile(checkpointer=MemorySaver())


@lru_cache
def get_graph():
    """Process-wide compiled graph; MemorySaver handles many runs by thread_id."""
    return build_graph()
