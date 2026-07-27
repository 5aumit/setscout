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


class SearchBrief(BaseModel):
    """The safe, read-only request summary retained with a Run."""

    purpose: str
    domain: str
    data_type: str
    requirements: str = ""


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
    """Public Result data retained after a Run completes."""

    evaluations: list[CandidateEvaluation]
    overview: str
    candidates: list[ResultCandidate] = Field(default_factory=list)


class ResultCandidate(BaseModel):
    """The safe dataset identity needed to act on a ranked Result."""

    id: str
    name: str
    source: str
    url: str


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
        self._candidates: list[DatasetCandidate] = []
        self._results: RunResults | None = None

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

    def begin_next_stage(self) -> None:
        """Mark the next user-facing Stage as running."""
        if self._next_stage_index >= len(STAGES):
            raise ValueError("all Stages have already started")
        self.begin_stage(STAGES[self._next_stage_index])

    @property
    def is_terminal(self) -> bool:
        return self._terminal is not None

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
        for node_name, patch in updates:
            self.consume(node_name, patch)
        if self._terminal is None:
            raise ValueError("pipeline ended before producing a terminal evaluation outcome")
        return self._record(self._results)

    def consume(self, node_name: str, patch: dict) -> RunRecord:
        """Apply one completed pipeline-stage patch and return the current Run snapshot."""
        try:
            stage = self._node_stages[node_name]
        except KeyError as exc:
            raise ValueError(f"unknown pipeline update: {node_name}") from exc
        if self.stage_history[stage] is StageLifecycle.WAITING:
            self.begin_stage(stage)
        elif self.stage_history[stage] is not StageLifecycle.RUNNING:
            raise ValueError(f"{stage} cannot receive an update from {self.stage_history[stage]}")

        if stage is Stage.PREPARE:
            self.activity(stage, "Prepared the Search Brief.")
            lifecycle = self._warning_or_completed(patch)
            if lifecycle is StageLifecycle.COMPLETED_WITH_WARNINGS:
                self.limitation("The Search Brief used a fallback interpretation of the request.")
            self.finish_stage(stage, lifecycle)
        elif stage is Stage.SEARCH:
            self._candidates = patch.get("candidates", [])
            counts = [Count(label="dataset candidates", value=len(self._candidates))]
            self.activity(stage, "Searched the configured dataset sources.", counts)
            lifecycle = self._warning_or_completed(patch)
            if lifecycle is StageLifecycle.COMPLETED_WITH_WARNINGS:
                self.limitation(
                    "One or more configured dataset sources could not be fully searched."
                )
            self.finish_stage(stage, lifecycle)
        elif stage is Stage.EVIDENCE:
            self._candidates = patch.get("candidates", self._candidates)
            fetched = sum(bool(candidate.evidence_docs) for candidate in self._candidates)
            self.activity(
                stage,
                "Gathered available documentation evidence.",
                [Count(label="documentation records", value=fetched)],
            )
            lifecycle = (
                StageLifecycle.COMPLETED
                if not self._candidates or fetched == len(self._candidates)
                else StageLifecycle.COMPLETED_WITH_WARNINGS
            )
            if lifecycle is StageLifecycle.COMPLETED_WITH_WARNINGS:
                self.limitation("Some candidate documentation was unavailable during evaluation.")
            self.finish_stage(stage, lifecycle)
        else:
            self.activity(stage, "Evaluated candidates against the Search Brief.")
            if patch.get("evaluation_failed") or (
                not has_complete_ranking(self._candidates, patch.get("evaluations", []))
                and self._candidates
            ):
                self.finish_stage(stage, StageLifecycle.FAILED)
                self.terminal(RunOutcome.FAILED)
            elif not self._candidates and not self._has_run_limitation():
                self.finish_stage(stage, StageLifecycle.COMPLETED)
                self.terminal(RunOutcome.EMPTY_RESULTS)
            else:
                self.finish_stage(stage, StageLifecycle.COMPLETED)
                self._results = RunResults(
                    evaluations=patch["evaluations"],
                    overview=self._results_overview(),
                    candidates=[
                        ResultCandidate(
                            id=candidate.id,
                            name=candidate.name,
                            source=candidate.source,
                            url=candidate.url,
                        )
                        for candidate in self._candidates
                    ],
                )
                self.terminal(
                    RunOutcome.COMPLETED_WITH_WARNINGS
                    if self._has_run_limitation()
                    else RunOutcome.COMPLETED
                )
        return self.snapshot()

    def snapshot(self) -> RunRecord:
        """Return the current user-safe Run state while it is still in progress."""
        return RunRecord(
            events=self.events.copy(),
            outcome=self._terminal or RunOutcome.COMPLETED,
            stage_history=self.stage_history.copy(),
            results=self._results,
        )

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

    def _results_overview(self) -> str:
        count = len(self._candidates)
        if count == 1:
            return "1 dataset ranked against your Search Brief."
        return f"{count} datasets ranked against your Search Brief."

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
