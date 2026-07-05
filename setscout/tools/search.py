from __future__ import annotations

import asyncio

from huggingface_hub import list_datasets

from setscout.models import DatasetCandidate, SearchSpec, normalize_prioritized_sources

SEARCH_LIMIT_PER_SOURCE = 10


def _first_attr(obj, *names, default=None):
    """Return the first non-None attribute from obj, trying names in order."""
    for name in names:
        val = getattr(obj, name, None)
        if val is not None:
            return val
    return default


def _search_query_candidates(spec: SearchSpec) -> list[str]:
    """Short queries work best; try expanded terms in order until one hits."""
    parts = [p.strip() for p in list(spec.expanded_keywords) + list(spec.mesh_terms) if p.strip()]
    if not parts:
        return ["dataset"]
    seen: set[str] = set()
    candidates: list[str] = []
    for part in parts[:5]:
        key = part.lower()
        if key not in seen:
            candidates.append(part)
            seen.add(key)
    return candidates


def _hf_to_candidate(info) -> DatasetCandidate:
    repo_id = info.id
    return DatasetCandidate(
        id=f"hf-{repo_id}",
        source="huggingface",
        name=repo_id.split("/")[-1],
        url=f"https://huggingface.co/datasets/{repo_id}",
        raw_metadata={
            "repo_id": repo_id,
            "downloads": getattr(info, "downloads", None),
            "likes": getattr(info, "likes", None),
            "tags": list(getattr(info, "tags", None) or []),
            "description": (getattr(info, "description", None) or "")[:500],
        },
    )


def _kaggle_to_candidate(ds) -> DatasetCandidate:
    ref = ds.ref
    return DatasetCandidate(
        id=f"kaggle-{ref.replace('/', '-')}",
        source="kaggle",
        name=getattr(ds, "title", None) or ref.split("/")[-1],
        url=f"https://www.kaggle.com/datasets/{ref}",
        raw_metadata={
            "ref": ref,
            "title": getattr(ds, "title", None),
            "subtitle": getattr(ds, "subtitle", None),
            "creator": _first_attr(ds, "creator_name", "creatorName"),
            "total_votes": _first_attr(ds, "vote_count", "totalVotes"),
            "total_downloads": _first_attr(ds, "download_count", "totalDownloads"),
            "last_updated": str(_first_attr(ds, "last_updated", "lastUpdated", default="")),
        },
    )


def _search_huggingface_sync(spec: SearchSpec, limit: int) -> list[DatasetCandidate]:
    for query in _search_query_candidates(spec):
        infos = list(list_datasets(search=query, sort="downloads", limit=limit))
        if infos:
            return [_hf_to_candidate(i) for i in infos]
    return []


def _search_kaggle_sync(spec: SearchSpec, limit: int) -> list[DatasetCandidate]:
    # The Kaggle package can require credentials at import time; keep that dependency
    # behind the Kaggle path so HuggingFace-only searches still import cleanly.
    from kaggle.api.kaggle_api_extended import KaggleApi

    api = KaggleApi()
    api.authenticate()
    for query in _search_query_candidates(spec):
        datasets = api.dataset_list(search=query, sort_by="votes", page=1) or []
        if datasets:
            return [_kaggle_to_candidate(d) for d in datasets[:limit]]
    return []


def _interleave_by_source(
    ordered_results: dict[str, list[DatasetCandidate]],
    ordered_sources: list[str],
) -> list[DatasetCandidate]:
    interleaved: list[DatasetCandidate] = []
    max_len = max((len(ordered_results[source]) for source in ordered_sources), default=0)
    for index in range(max_len):
        for source in ordered_sources:
            candidates = ordered_results[source]
            if index < len(candidates):
                interleaved.append(candidates[index])
    return interleaved


async def search_huggingface(
    spec: SearchSpec, limit: int = SEARCH_LIMIT_PER_SOURCE
) -> list[DatasetCandidate]:
    return await asyncio.to_thread(_search_huggingface_sync, spec, limit)


async def search_kaggle(
    spec: SearchSpec, limit: int = SEARCH_LIMIT_PER_SOURCE
) -> list[DatasetCandidate]:
    return await asyncio.to_thread(_search_kaggle_sync, spec, limit)


async def search_all_sources(spec: SearchSpec) -> tuple[list[DatasetCandidate], list[str]]:
    sources = normalize_prioritized_sources(spec.prioritized_sources)
    tasks: dict[str, asyncio.Task] = {}
    if "huggingface" in sources:
        tasks["huggingface"] = asyncio.create_task(search_huggingface(spec))
    if "kaggle" in sources:
        tasks["kaggle"] = asyncio.create_task(search_kaggle(spec))

    results_by_source: dict[str, list[DatasetCandidate]] = {source: [] for source in sources}
    search_logs: list[str] = []
    for source, task in tasks.items():
        try:
            found = await task
            results_by_source[source] = found
            search_logs.append(f"searcher: {source} returned {len(found)} hits")
        except Exception as exc:
            search_logs.append(f"searcher: {source} failed - {type(exc).__name__}: {exc}")
    candidates = _interleave_by_source(results_by_source, sources)
    return candidates, search_logs
