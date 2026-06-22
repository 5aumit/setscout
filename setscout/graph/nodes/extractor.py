from __future__ import annotations

from setscout.graph.state import SetScoutState, log
from setscout.models import DatasetCandidate, ExtractedFacts


def node_extractor(state: SetScoutState) -> dict:
    updated: list[DatasetCandidate] = []
    for c in state["candidates"]:
        facts = ExtractedFacts(
            num_samples=10_000,
            size_in_gb=1.2,
            label_methodology="expert-annotated (stub)",
            metadata_fields=["patient_id", "label"],
            access_requirements="public",
            class_distribution="70/30",
        )
        updated.append(c.model_copy(update={"extracted_facts": facts}))
    return {"candidates": updated, **log("extractor: facts attached")}
