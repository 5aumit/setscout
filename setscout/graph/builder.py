from __future__ import annotations

from functools import partial

from langgraph.graph import END, START, StateGraph

from setscout.graph.nodes.decomposer import node_decomposer
from setscout.graph.nodes.extractor import node_extractor
from setscout.graph.nodes.issue_hunter import node_issue_hunter
from setscout.graph.nodes.llm import make_llm
from setscout.graph.nodes.reporter import node_reporter
from setscout.graph.nodes.scorer import node_scorer
from setscout.graph.nodes.searcher import node_searcher
from setscout.graph.state import SetScoutState


def build_setscout_graph(api_key: str | None):
    llm = make_llm(api_key) if api_key else None

    g = StateGraph(SetScoutState)
    g.add_node("decomposer", partial(node_decomposer, llm=llm))
    g.add_node("searcher", node_searcher)
    g.add_node("extractor", node_extractor)
    g.add_node("issue_hunter", node_issue_hunter)
    g.add_node("scorer", partial(node_scorer, llm=llm))
    g.add_node("reporter", node_reporter)

    g.add_edge(START, "decomposer")
    g.add_edge("decomposer", "searcher")
    g.add_edge("searcher", "extractor")
    g.add_edge("extractor", "issue_hunter")
    g.add_edge("issue_hunter", "scorer")
    g.add_edge("scorer", "reporter")
    g.add_edge("reporter", END)

    return g.compile()
