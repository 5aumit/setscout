from __future__ import annotations

from setscout.graph.state import SetScoutState, log
from setscout.models import DatasetCandidate


def node_issue_hunter(state: SetScoutState) -> dict:
    updated: list[DatasetCandidate] = []
    for c in state["candidates"]:
        issues = ["stub: class imbalance noted in one citing paper"] if "benchmark" in c.name else []
        updated.append(c.model_copy(update={"known_issues": issues}))
    return {"candidates": updated, **log("issue_hunter: issues attached")}
