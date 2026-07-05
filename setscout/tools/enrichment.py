from __future__ import annotations

import asyncio
import os
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from setscout.models import DatasetCandidate

T = TypeVar("T")

DEFAULT_ENRICHMENT_CONCURRENCY = 2


async def gather_outcomes(
    candidates: list[DatasetCandidate],
    worker: Callable[[DatasetCandidate], Awaitable[tuple[str, T | None]]],
) -> dict[str, T | None]:
    limit = int(os.environ.get("SETSCOUT_ENRICHMENT_CONCURRENCY", DEFAULT_ENRICHMENT_CONCURRENCY))
    semaphore = asyncio.Semaphore(max(1, limit))

    async def _run(candidate: DatasetCandidate):
        async with semaphore:
            return await worker(candidate)

    results = await asyncio.gather(*(_run(c) for c in candidates), return_exceptions=True)
    out: dict[str, T | None] = {}
    for candidate, result in zip(candidates, results, strict=True):
        if isinstance(result, BaseException):
            out[candidate.id] = None
        else:
            cid, value = result
            out[cid] = value
    return out
