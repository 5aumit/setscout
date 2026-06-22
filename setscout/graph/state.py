from __future__ import annotations

from operator import add
from typing import Annotated, TypedDict

from setscout.models import DatasetCandidate, ScoredDataset, SearchSpec, UserQuery


class SetScoutState(TypedDict, total=False):
    query: UserQuery
    search_spec: SearchSpec
    candidates: list[DatasetCandidate]
    scored_datasets: list[ScoredDataset]
    report: str
    logs: Annotated[list[str], add]


def log(msg: str) -> dict:
    return {"logs": [msg]}
