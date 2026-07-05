from __future__ import annotations

import os
from functools import partial

from langgraph.graph import END, START, StateGraph

from setscout.graph.nodes.decomposer import node_decomposer
from setscout.graph.nodes.evaluator import node_evaluator
from setscout.graph.nodes.gather_evidence import node_gather_evidence
from setscout.graph.nodes.llm import DEFAULT_DECOMPOSER_MODEL, DEFAULT_REPORT_MODEL, make_llm
from setscout.graph.nodes.searcher import node_searcher
from setscout.graph.state import SetScoutState


def build_setscout_graph(api_key: str):
    decomposer_llm = make_llm(
        api_key,
        model=os.environ.get("SETSCOUT_DECOMPOSER_MODEL", DEFAULT_DECOMPOSER_MODEL),
    )
    report_llm = make_llm(
        api_key,
        model=os.environ.get("SETSCOUT_REPORT_MODEL", DEFAULT_REPORT_MODEL),
    )

    g = StateGraph(SetScoutState)
    g.add_node("decomposer", partial(node_decomposer, llm=decomposer_llm))
    g.add_node("searcher", node_searcher)
    g.add_node("gather_evidence", node_gather_evidence)
    g.add_node("evaluator", partial(node_evaluator, llm=report_llm))

    g.add_edge(START, "decomposer")
    g.add_edge("decomposer", "searcher")
    g.add_edge("searcher", "gather_evidence")
    g.add_edge("gather_evidence", "evaluator")
    g.add_edge("evaluator", END)

    return g.compile()
