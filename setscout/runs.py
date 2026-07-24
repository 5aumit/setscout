"""Presentation-independent Run events and the adapter that produces them."""

from __future__ import annotations

from collections.abc import Iterable
from enum import StrEnum
from typing import Literal, TypeAlias

from pydantic import BaseModel, Field

from setscout.models import CandidateEvaluation, DatasetCandidate, has_complete_ranking


class Stage(StrEnum):
    PREPARE = "prepare_search_brief"
    SEARCH = "search_dataset_sources"
    EVIDENCE = "gather_documentation_evidence"
    EVALUATE = "evaluate_and_rank_candidates"


STAGES = tuple(Stage)


class StageLifecycle(StrEnum):
    WAITING = "waiting"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    FAILED = "failed"


class RunOutcome(StrEnum):
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    EMPTY_RESULTS = "empty_results"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Count(BaseModel):
    label: str
    value: int


class QueuedEvent(BaseModel):
    kind: Literal["queued"] = "queued"


class StageEvent(BaseModel):
    kind: Literal["stage"] = "stage"
    stage: Stage
    lifecycle: StageLifecycle
    counts: list[Count] = Field(default_factory=list)


class ActivityEvent(BaseModel):
    kind: Literal["activity"] = "activity"
    stage: Stage
    message: str
    counts: list[Count] = Field(default_factory=list)


class LimitationEvent(BaseModel):
    kind: Literal["limitation"] = "limitation"
    scope: Literal["run", "candidate"]
    message: str


class TerminalEvent(BaseModel):
    kind: Literal["terminal"] = "terminal"
    outcome: RunOutcome


RunEvent: TypeAlias = QueuedEvent | StageEvent | ActivityEvent | LimitationEvent | TerminalEvent


class RunResults(BaseModel):
    evaluations: list[CandidateEvaluation]
    overview: str


class RunRecord(BaseModel):
    events: list[RunEvent]
    outcome: RunOutcome
    stage_history: dict[Stage, StageLifecycle]
    results: RunResults | None = None


PipelineUpdate: TypeAlias = tuple[str, dict]


class RunEventAdapter:
    """Translate pipeline facts into the stable, user-facing Run event contract."""

    _node_stages = {
        "decomposer": Stage.PREPARE,
        "searcher": Stage.SEARCH,
        "gather_evidence": Stage.EVIDENCE,
        "evaluator": Stage.EVALUATE,
    }

    def __init__(self) -> None:
        self.events: list[RunEvent] = []
        self.stage_history = {stage: StageLifecycle.WAITING for stage in STAGES}
        self._started = False
        self._terminal: RunOutcome | None = None
        self._next_stage_index = 0

    def start(self) -> None:
        if self._started:
            raise ValueError("a Run can only be queued once")
        self._started = True
        self.events.append(QueuedEvent())
        self.events.extend(
            StageEvent(stage=stage, lifecycle=StageLifecycle.WAITING) for stage in STAGES
        )

    def begin_stage(self, stage: Stage) -> None:
        if not self._started or self._terminal:
            raise ValueError("a queued, active Run is required")
        if self._next_stage_index >= len(STAGES) or STAGES[self._next_stage_index] is not stage:
            raise ValueError("Stages must start in their fixed user-facing order")
        if self.stage_history[stage] is not StageLifecycle.WAITING:
            raise ValueError(f"{stage} cannot start from {self.stage_history[stage]}")
        self.stage_history[stage] = StageLifecycle.RUNNING
        self.events.append(StageEvent(stage=stage, lifecycle=StageLifecycle.RUNNING))

    def activity(self, stage: Stage, message: str, counts: list[Count] | None = None) -> None:
        if self.stage_history[stage] is not StageLifecycle.RUNNING:
            raise ValueError("activity updates require a running Stage")
        self.events.append(ActivityEvent(stage=stage, message=message, counts=counts or []))

    def limitation(self, message: str) -> None:
        self.events.append(LimitationEvent(scope="run", message=message))

    def finish_stage(self, stage: Stage, lifecycle: StageLifecycle) -> None:
        allowed = {
            StageLifecycle.COMPLETED,
            StageLifecycle.COMPLETED_WITH_WARNINGS,
            StageLifecycle.FAILED,
        }
        if lifecycle not in allowed or self.stage_history[stage] is not StageLifecycle.RUNNING:
            raise ValueError("a running Stage must end in an allowed terminal lifecycle")
        self.stage_history[stage] = lifecycle
        self.events.append(StageEvent(stage=stage, lifecycle=lifecycle))
        self._next_stage_index += 1

    def terminal(self, outcome: RunOutcome) -> None:
        if not self._started or self._terminal:
            raise ValueError("a Run can only have one terminal outcome")
        self._terminal = outcome
        self.events.append(TerminalEvent(outcome=outcome))

    def cancel(self) -> RunRecord:
        """End an active Run cooperatively without producing incomplete Results."""
        self.terminal(RunOutcome.CANCELLED)
        return self._record(None)

    def adapt(self, updates: Iterable[PipelineUpdate]) -> RunRecord:
        """Adapt ordered LangGraph node patches without exposing their logs or names."""
        self.start()
        candidates: list[DatasetCandidate] = []
        results: RunResults | None = None

        for node_name, patch in updates:
            try:
                stage = self._node_stages[node_name]
            except KeyError as exc:
                raise ValueError(f"unknown pipeline update: {node_name}") from exc
            self.begin_stage(stage)

            if stage is Stage.PREPARE:
                self.activity(stage, "Prepared the Search Brief.")
                lifecycle = self._warning_or_completed(patch)
                if lifecycle is StageLifecycle.COMPLETED_WITH_WARNINGS:
                    self.limitation(
                        "The Search Brief used a fallback interpretation of the request."
                    )
                self.finish_stage(stage, lifecycle)
            elif stage is Stage.SEARCH:
                candidates = patch.get("candidates", [])
                counts = [Count(label="dataset candidates", value=len(candidates))]
                self.activity(stage, "Searched the configured dataset sources.", counts)
                lifecycle = self._warning_or_completed(patch)
                if lifecycle is StageLifecycle.COMPLETED_WITH_WARNINGS:
                    self.limitation(
                        "One or more configured dataset sources could not be fully searched."
                    )
                self.finish_stage(stage, lifecycle)
            elif stage is Stage.EVIDENCE:
                candidates = patch.get("candidates", candidates)
                fetched = sum(bool(candidate.evidence_docs) for candidate in candidates)
                counts = [Count(label="documentation records", value=fetched)]
                self.activity(stage, "Gathered available documentation evidence.", counts)
                lifecycle = (
                    StageLifecycle.COMPLETED
                    if not candidates or fetched == len(candidates)
                    else StageLifecycle.COMPLETED_WITH_WARNINGS
                )
                if lifecycle is StageLifecycle.COMPLETED_WITH_WARNINGS:
                    self.limitation(
                        "Some candidate documentation was unavailable during evaluation."
                    )
                self.finish_stage(stage, lifecycle)
            else:
                self.activity(stage, "Evaluated candidates against the Search Brief.")
                if patch.get("evaluation_failed") or not has_complete_ranking(
                    candidates, patch.get("evaluations", [])
                ) and candidates:
                    self.finish_stage(stage, StageLifecycle.FAILED)
                    self.terminal(RunOutcome.FAILED)
                    return self._record(None)
                self.finish_stage(stage, StageLifecycle.COMPLETED)
                if not candidates:
                    if self._has_run_limitation():
                        results = RunResults(evaluations=[], overview=patch.get("report", ""))
                        break
                    self.terminal(RunOutcome.EMPTY_RESULTS)
                    return self._record(None)
                results = RunResults(
                    evaluations=patch["evaluations"], overview=patch.get("report", "")
                )

        if results is None:
            raise ValueError("pipeline ended before producing a terminal evaluation outcome")
        self.terminal(
            RunOutcome.COMPLETED_WITH_WARNINGS
            if self._has_run_limitation()
            else RunOutcome.COMPLETED
        )
        return self._record(results)

    def _record(self, results: RunResults | None) -> RunRecord:
        assert self._terminal is not None
        return RunRecord(
            events=self.events,
            outcome=self._terminal,
            stage_history=self.stage_history,
            results=results,
        )

    def _has_run_limitation(self) -> bool:
        return any(event.kind == "limitation" and event.scope == "run" for event in self.events)

    @staticmethod
    def _warning_or_completed(patch: dict) -> StageLifecycle:
        logs = patch.get("logs", [])
        return (
            StageLifecycle.COMPLETED_WITH_WARNINGS
            if any(
                word in entry.lower()
                for entry in logs
                for word in ("failed", "fallback", "skipped")
            )
            else StageLifecycle.COMPLETED
        )
