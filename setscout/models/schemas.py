from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class UserQuery(BaseModel):
    purpose: str
    domain: str
    data_type: str
    requirements: Optional[str] = None
    additional_notes: Optional[str] = None
    exclude_datasets: list[str] = Field(default_factory=list)


class SearchSpec(BaseModel):
    expanded_keywords: list[str] = Field(description="Synonyms and related terms")
    mesh_terms: list[str] = Field(default_factory=list)
    prioritized_sources: list[str] = Field(description="huggingface and/or kaggle")
    hard_constraints: dict[str, Any] = Field(default_factory=dict)


DEFAULT_SOURCES = ("huggingface", "kaggle")
_ALLOWED_SOURCES = frozenset(DEFAULT_SOURCES)


def normalize_prioritized_sources(sources: list[str]) -> list[str]:
    normalized = [s.lower().strip() for s in sources if s.lower().strip() in _ALLOWED_SOURCES]
    return normalized or list(DEFAULT_SOURCES)


class ExtractedFacts(BaseModel):
    size_in_gb: Optional[float] = None
    num_samples: Optional[int] = None
    label_methodology: Optional[str] = None
    metadata_fields: list[str] = Field(default_factory=list)
    access_requirements: Optional[str] = None
    class_distribution: Optional[str] = None


class DatasetCandidate(BaseModel):
    id: str
    source: str
    name: str
    url: str
    raw_metadata: dict[str, Any] = Field(default_factory=dict)
    extracted_facts: Optional[ExtractedFacts] = None
    known_issues: list[str] = Field(default_factory=list)


class Layer1Scores(BaseModel):
    size_fit: float = Field(ge=0, le=1)
    metadata_fit: float = Field(ge=0, le=1)
    access_fit: float = Field(ge=0, le=1)


class Layer2Scores(BaseModel):
    label_quality: float = Field(ge=0, le=1)
    issue_severity: float = Field(ge=0, le=1, description="1 = no serious issues")
    purpose_fit: float = Field(ge=0, le=1)
    reasoning: str = ""


class ScoreBreakdown(BaseModel):
    layer1: Layer1Scores
    layer2: Layer2Scores
    final_score: float = Field(ge=0, le=1)


class ScoredDataset(BaseModel):
    candidate: DatasetCandidate
    scores: ScoreBreakdown
