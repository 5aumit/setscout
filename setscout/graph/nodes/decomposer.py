from __future__ import annotations

import re

from setscout.graph.state import SetScoutState, log
from setscout.models import SearchConstraints, SearchSpec, UserQuery, normalize_prioritized_sources


def _extract_min_samples(text: str) -> int | None:
    match = re.search(r"at least\s+([\d,]+)\s+(?:examples|samples|records)", text, re.I)
    if not match:
        return None
    return int(match.group(1).replace(",", ""))


def _fallback_constraints(q: UserQuery) -> SearchConstraints:
    text = " ".join([q.requirements or "", q.additional_notes or ""]).lower()
    return SearchConstraints(
        min_samples=_extract_min_samples(text),
        access="public" if "public" in text else None,
    )


def _fallback_search_spec(q: UserQuery) -> SearchSpec:
    keywords = [
        q.domain,
        q.data_type,
        q.purpose,
        *(q.requirements or "").split(",")[:2],
    ]
    return SearchSpec(
        expanded_keywords=[item.strip() for item in keywords if item.strip()],
        prioritized_sources=normalize_prioritized_sources([]),
        hard_constraints=_fallback_constraints(q),
    )


def node_decomposer(state: SetScoutState, *, llm) -> dict:
    q = state["query"]
    structured = llm.with_structured_output(SearchSpec)
    try:
        spec = structured.invoke(
            f"""Expand this dataset search into a SearchSpec.
Purpose: {q.purpose}
Domain: {q.domain}
Data type: {q.data_type}
Requirements: {q.requirements or 'none'}
Notes: {q.additional_notes or 'none'}
Pick prioritized_sources from: huggingface, kaggle (both unless requirements suggest one).
Extract hard_constraints using the typed schema fields only."""
        )
        message = "decomposer: SearchSpec ready"
    except Exception as exc:
        spec = _fallback_search_spec(q)
        message = f"decomposer: LLM failed, used fallback SearchSpec ({type(exc).__name__})"
    spec.prioritized_sources = normalize_prioritized_sources(spec.prioritized_sources)
    return {"search_spec": spec, **log(message)}
