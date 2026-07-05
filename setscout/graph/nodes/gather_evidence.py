from __future__ import annotations

import os

from setscout.graph.state import SetScoutState, log
from setscout.models import DatasetCandidate, EvidenceDoc
from setscout.tools.async_utils import run_async
from setscout.tools.documents import fetch_dataset_card
from setscout.tools.enrichment import gather_outcomes
from setscout.tools.prompt_context import format_batch_excerpt

DEFAULT_BATCH_EXCERPT_CHARS = 20000


async def _fetch_one(candidate: DatasetCandidate) -> tuple[str, str | None]:
    text = await fetch_dataset_card(candidate)
    return candidate.id, text or None


def node_gather_evidence(state: SetScoutState) -> dict:
    candidates = state["candidates"]
    max_chars = int(os.environ.get("SETSCOUT_BATCH_EXCERPT_CHARS", DEFAULT_BATCH_EXCERPT_CHARS))

    card_texts: dict[str, str | None] = run_async(gather_outcomes(candidates, _fetch_one))

    updated: list[DatasetCandidate] = []
    fetched = 0
    for c in candidates:
        text = card_texts.get(c.id)
        if text:
            excerpt = format_batch_excerpt(text, max_chars)
            updated.append(c.model_copy(update={
                "evidence_docs": [EvidenceDoc(kind="dataset_card", url=c.url, text=excerpt)],
            }))
            fetched += 1
        else:
            updated.append(c)

    return {"candidates": updated, **log(f"gather_evidence: {fetched}/{len(candidates)} cards fetched")}
