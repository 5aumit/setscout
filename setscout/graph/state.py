from __future__ import annotations

from operator import add
from typing import Annotated, TypedDict

from setscout.models import CandidateEvaluation, DatasetCandidate, SearchSpec, UserQuery


class SetScoutState(TypedDict, total=False):
    query: UserQuery
    search_spec: SearchSpec
    candidates: list[DatasetCandidate]
    evaluations: list[CandidateEvaluation]
    report: str
    evaluation_failed: bool
    logs: Annotated[list[str], add]


def log(msg: str) -> dict:
    return {"logs": [msg]}
