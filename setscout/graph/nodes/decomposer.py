from __future__ import annotations

from setscout.graph.state import SetScoutState, log
from setscout.models import SearchSpec, normalize_prioritized_sources


def node_decomposer(state: SetScoutState, *, llm=None) -> dict:
    q = state["query"]
    if llm is not None:
        structured = llm.with_structured_output(SearchSpec)
        spec = structured.invoke(
            f"""Expand this dataset search into a SearchSpec.
Purpose: {q.purpose}
Domain: {q.domain}
Data type: {q.data_type}
Requirements: {q.requirements or 'none'}
Notes: {q.additional_notes or 'none'}
Pick prioritized_sources from: huggingface, kaggle (both unless requirements suggest one).
Extract hard_constraints from requirements (e.g. min_samples, license)."""
        )
        spec.prioritized_sources = normalize_prioritized_sources(spec.prioritized_sources)
    else:
        spec = SearchSpec(
            expanded_keywords=[q.domain, q.data_type, *q.purpose.split()[:3]],
            mesh_terms=["stub-mesh"] if "medical" in q.domain.lower() else [],
            prioritized_sources=normalize_prioritized_sources([]),
            hard_constraints=(
                {"min_samples": 100}
                if q.requirements and "sample" in q.requirements.lower()
                else {}
            ),
        )
    return {"search_spec": spec, **log("decomposer: SearchSpec ready")}
