from __future__ import annotations

from setscout.graph.state import SetScoutState, log
from setscout.models import (
    DatasetCandidate,
    Layer1Scores,
    Layer2Scores,
    ScoreBreakdown,
    ScoredDataset,
    UserQuery,
)

LAYER1_WEIGHTS = {"size_fit": 0.15, "metadata_fit": 0.15, "access_fit": 0.10}
LAYER2_WEIGHTS = {"label_quality": 0.25, "issue_severity": 0.15, "purpose_fit": 0.20}


def _layer1_score(c: DatasetCandidate) -> Layer1Scores:
    facts = c.extracted_facts
    size_fit = 0.8 if facts and (facts.num_samples or 0) >= 1000 else 0.4
    metadata_fit = 0.9 if facts and len(facts.metadata_fields) >= 2 else 0.5
    access_fit = 1.0 if facts and facts.access_requirements == "public" else 0.6
    return Layer1Scores(size_fit=size_fit, metadata_fit=metadata_fit, access_fit=access_fit)


def _layer2_score(
    c: DatasetCandidate, query: UserQuery, *, structured=None
) -> Layer2Scores:
    if structured is not None:
        return structured.invoke(
            f"""Score this dataset for the user's purpose (0-1 each field).
Purpose: {query.purpose}
Dataset: {c.name} ({c.source})
Facts: {c.extracted_facts}
Issues: {c.known_issues}"""
        )
    issue_penalty = 0.3 if c.known_issues else 0.0
    return Layer2Scores(
        label_quality=0.75,
        issue_severity=max(0.0, 1.0 - issue_penalty),
        purpose_fit=0.7,
        reasoning="stub layer-2 (set GEMINI_API_KEY in .env for LLM judging)",
    )


def node_scorer(state: SetScoutState, *, llm=None) -> dict:
    query = state["query"]
    structured = llm.with_structured_output(Layer2Scores) if llm else None
    scored: list[ScoredDataset] = []
    for c in state["candidates"]:
        l1 = _layer1_score(c)
        l2 = _layer2_score(c, query, structured=structured)
        l1_scores = l1.model_dump()
        l2_scores = l2.model_dump()
        final = sum(l1_scores[k] * w for k, w in LAYER1_WEIGHTS.items()) + sum(
            l2_scores[k] * w for k, w in LAYER2_WEIGHTS.items()
        )
        scored.append(
            ScoredDataset(
                candidate=c,
                scores=ScoreBreakdown(layer1=l1, layer2=l2, final_score=round(final, 3)),
            )
        )
    scored.sort(key=lambda s: s.scores.final_score, reverse=True)
    return {"scored_datasets": scored, **log("scorer: ranked datasets")}
