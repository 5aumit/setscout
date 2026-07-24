"""Reviewed, offline practice data for the Ledger presentation."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from setscout.runs import RunRecord, SearchBrief


class PracticeRun(BaseModel):
    """A versioned replay payload containing only presentation-safe fields."""

    version: int
    search_brief: SearchBrief
    run: RunRecord


_PRACTICE_RUN_PATH = Path(__file__).with_name("fixtures") / "practice_run_v1.json"


def load_practice_run() -> PracticeRun:
    """Load the checked-in Run used for local, no-network Ledger practice."""
    return PracticeRun.model_validate(json.loads(_PRACTICE_RUN_PATH.read_text()))
