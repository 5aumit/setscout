from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class UserQuery(BaseModel):
    purpose: str
    domain: str
    data_type: str
    requirements: str | None = None
    additional_notes: str | None = None
    exclude_datasets: list[str] = Field(default_factory=list)


class SearchConstraints(BaseModel):
    min_samples: int | None = None
    access: str | None = None


class SearchSpec(BaseModel):
    expanded_keywords: list[str] = Field(description="Synonyms and related terms")
    mesh_terms: list[str] = Field(default_factory=list)
    prioritized_sources: list[str] = Field(description="huggingface and/or kaggle")
    hard_constraints: SearchConstraints = Field(default_factory=SearchConstraints)

    @field_validator("hard_constraints", mode="before")
    @classmethod
    def _normalize_constraints(cls, value):
        return value or {}


DEFAULT_SOURCES = ("huggingface", "kaggle")
_ALLOWED_SOURCES = frozenset(DEFAULT_SOURCES)


def normalize_prioritized_sources(sources: list[str]) -> list[str]:
    normalized = [s.lower().strip() for s in sources if s.lower().strip() in _ALLOWED_SOURCES]
    return normalized or list(DEFAULT_SOURCES)


# Kept for future per-candidate RAG enrichment (long-term pipeline)
class ExtractedFacts(BaseModel):
    size_in_gb: float | None = Field(None, description="Total dataset size in gigabytes.")
    num_samples: int | None = Field(None, description="Total number of samples or records.")
    label_methodology: str | None = Field(
        None,
        description="How labels were created, such as expert, crowd, or programmatic labels.",
    )
    metadata_fields: list[str] = Field(
        default_factory=list,
        description="Available metadata column or field names.",
    )
    access_requirements: str | None = Field(
        None,
        description="Access level: public, registration required, restricted, etc.",
    )
    class_distribution: str | None = Field(
        None,
        description="Class balance summary, such as 70/30, balanced, or severely imbalanced.",
    )


# Kept for future per-candidate RAG enrichment (long-term pipeline)
class DatasetEnrichment(BaseModel):
    facts: ExtractedFacts
    issues: list[str] = Field(
        default_factory=list,
        description="Explicit documentation-backed issues. Empty if none found.",
    )


class EvidenceDoc(BaseModel):
    kind: Literal["dataset_card", "paper", "discussion"]
    url: str
    text: str


class DatasetCandidate(BaseModel):
    id: str
    source: str
    name: str
    url: str
    raw_metadata: dict[str, Any] = Field(default_factory=dict)
    evidence_docs: list[EvidenceDoc] = Field(default_factory=list)


class IssueFinding(BaseModel):
    summary: str
    source_kind: Literal["dataset_card", "paper", "discussion"]
    source_url: str
    severity: Literal["low", "medium", "high"] | None = None


class RequirementCheck(BaseModel):
    requirement: str
    status: Literal["met", "partial", "not_met", "unknown"]
    note: str = ""


class CandidateEvaluation(BaseModel):
    candidate_id: str
    rank: int
    fit_summary: str
    requirement_checks: list[RequirementCheck] = Field(default_factory=list)
    known_issues: list[IssueFinding] = Field(default_factory=list)


class PipelineResult(BaseModel):
    evaluations: list[CandidateEvaluation]
    report_markdown: str
