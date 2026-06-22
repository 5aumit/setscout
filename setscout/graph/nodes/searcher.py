from __future__ import annotations

from setscout.graph.state import SetScoutState
from setscout.models import DatasetCandidate
from setscout.tools.async_utils import run_async
from setscout.tools.search import search_all_sources


def _apply_exclude(candidates: list[DatasetCandidate], exclude: set[str]) -> list[DatasetCandidate]:
    if not exclude:
        return candidates
    kept: list[DatasetCandidate] = []
    for c in candidates:
        haystack = " ".join(
            [c.name, c.id, c.url, str(c.raw_metadata.get("repo_id", "")), str(c.raw_metadata.get("ref", ""))]
        ).lower()
        if not any(ex in haystack for ex in exclude):
            kept.append(c)
    return kept


def node_searcher(state: SetScoutState) -> dict:
    spec = state["search_spec"]
    candidates, search_logs = run_async(search_all_sources(spec))
    exclude = {x.strip().lower() for x in state["query"].exclude_datasets if x.strip()}
    filtered = _apply_exclude(candidates, exclude)
    logs = search_logs + [f"searcher: {len(filtered)} candidates after exclusions"]
    return {"candidates": filtered, "logs": logs}
