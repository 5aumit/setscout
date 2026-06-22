from __future__ import annotations

import asyncio

from setscout.models import DatasetCandidate, SearchSpec, normalize_prioritized_sources

SEARCH_LIMIT_PER_SOURCE = 10


def _search_query(spec: SearchSpec) -> str:
    parts = list(spec.expanded_keywords) + list(spec.mesh_terms)
    return " ".join(p.strip() for p in parts if p.strip())[:200] or "dataset"


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
            "creator": getattr(ds, "creatorName", None),
            "total_votes": getattr(ds, "totalVotes", None),
            "total_downloads": getattr(ds, "totalDownloads", None),
            "last_updated": str(getattr(ds, "lastUpdated", "")),
        },
    )


def _search_huggingface_sync(spec: SearchSpec, limit: int) -> list[DatasetCandidate]:
    from huggingface_hub import list_datasets

    query = _search_query(spec)
    infos = list(list_datasets(search=query, sort="downloads", direction=-1, limit=limit))
    return [_hf_to_candidate(i) for i in infos]


def _search_kaggle_sync(spec: SearchSpec, limit: int) -> list[DatasetCandidate]:
    from kaggle.api.kaggle_api_extended import KaggleApi

    api = KaggleApi()
    api.authenticate()
    query = _search_query(spec)
    datasets = api.dataset_list(search=query, sort_by="votes", page_size=limit)
    return [_kaggle_to_candidate(d) for d in datasets]


async def search_huggingface(
    spec: SearchSpec, limit: int = SEARCH_LIMIT_PER_SOURCE
) -> list[DatasetCandidate]:
    return await asyncio.to_thread(_search_huggingface_sync, spec, limit)


async def search_kaggle(
    spec: SearchSpec, limit: int = SEARCH_LIMIT_PER_SOURCE
) -> list[DatasetCandidate]:
    return await asyncio.to_thread(_search_kaggle_sync, spec, limit)


async def search_all_sources(spec: SearchSpec) -> tuple[list[DatasetCandidate], list[str]]:
    sources = set(normalize_prioritized_sources(spec.prioritized_sources))
    tasks: dict[str, asyncio.Task] = {}
    if "huggingface" in sources:
        tasks["huggingface"] = asyncio.create_task(search_huggingface(spec))
    if "kaggle" in sources:
        tasks["kaggle"] = asyncio.create_task(search_kaggle(spec))

    candidates: list[DatasetCandidate] = []
    search_logs: list[str] = []
    for source, task in tasks.items():
        try:
            found = await task
            candidates.extend(found)
            search_logs.append(f"searcher: {source} returned {len(found)} hits")
        except Exception as exc:
            search_logs.append(f"searcher: {source} failed — {type(exc).__name__}: {exc}")
    return candidates, search_logs
