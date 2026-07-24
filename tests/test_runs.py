from __future__ import annotations

import pytest
from pydantic import ValidationError

from setscout.models import (
    CandidateEvaluation,
    DatasetCandidate,
    EvidenceCitation,
    EvidenceDoc,
    RequirementCheck,
)
from setscout.runs import (
    RunEventAdapter,
    RunOutcome,
    Stage,
    StageLifecycle,
)


def _candidate(candidate_id: str) -> DatasetCandidate:
    return DatasetCandidate(
        id=candidate_id,
        source="huggingface",
        name=candidate_id,
        url=f"https://example.com/{candidate_id}",
    )


def _evaluation(candidate_id: str, rank: int) -> CandidateEvaluation:
    return CandidateEvaluation(
        candidate_id=candidate_id,
        rank=rank,
        fit_summary="A good fit for the stated use.",
        requirement_checks=[
            RequirementCheck(
                requirement="English text",
                status="met",
                citation=EvidenceCitation(
                    source_kind="dataset_card",
                    source_url="https://example.com/card",
                    excerpt="The dataset contains English text.",
                ),
            )
        ],
    )


def _completed_updates() -> list[tuple[str, dict[str, object]]]:
    candidate = _candidate("reviews").model_copy(
        update={
            "evidence_docs": [
                EvidenceDoc(
                    kind="dataset_card",
                    url="https://example.com/card",
                    text="The dataset contains English text.",
                )
            ]
        }
    )
    return [
        ("decomposer", {"search_spec": object()}),
        ("searcher", {"candidates": [candidate]}),
        ("gather_evidence", {"candidates": [candidate]}),
        ("evaluator", {"evaluations": [_evaluation(candidate.id, 1)], "report": "Overview"}),
    ]


def test_completed_run_emits_ordered_public_updates_and_structured_results():
    run = RunEventAdapter().adapt(_completed_updates())

    assert run.outcome is RunOutcome.COMPLETED
    assert run.results is not None
    assert [event.kind for event in run.events] == [
        "queued",
        *(["stage"] * 4),
        "stage",
        "activity",
        "stage",
        "stage",
        "activity",
        "stage",
        "stage",
        "activity",
        "stage",
        "stage",
        "activity",
        "stage",
        "terminal",
    ]
    assert [event.stage for event in run.events if event.kind == "stage"] == [
        Stage.PREPARE,
        Stage.SEARCH,
        Stage.EVIDENCE,
        Stage.EVALUATE,
        Stage.PREPARE,
        Stage.PREPARE,
        Stage.SEARCH,
        Stage.SEARCH,
        Stage.EVIDENCE,
        Stage.EVIDENCE,
        Stage.EVALUATE,
        Stage.EVALUATE,
    ]
    assert [event.lifecycle for event in run.events if event.kind == "stage"] == [
        StageLifecycle.WAITING,
        StageLifecycle.WAITING,
        StageLifecycle.WAITING,
        StageLifecycle.WAITING,
        StageLifecycle.RUNNING,
        StageLifecycle.COMPLETED,
        StageLifecycle.RUNNING,
        StageLifecycle.COMPLETED,
        StageLifecycle.RUNNING,
        StageLifecycle.COMPLETED,
        StageLifecycle.RUNNING,
        StageLifecycle.COMPLETED,
    ]
    assert run.results.evaluations[0].requirement_checks[0].citation is not None
    assert all(
        "decomposer" not in event.message for event in run.events if event.kind == "activity"
    )


def test_evaluator_failure_fails_run_and_suppresses_ranked_results():
    updates = _completed_updates()
    updates[-1] = ("evaluator", {"evaluation_failed": True})

    run = RunEventAdapter().adapt(updates)

    assert run.outcome is RunOutcome.FAILED
    assert run.results is None
    assert run.events[-1].kind == "terminal"
    assert run.events[-1].outcome is RunOutcome.FAILED
    assert run.stage_history[Stage.EVALUATE] is StageLifecycle.FAILED


@pytest.mark.parametrize(
    "lifecycle",
    [
        StageLifecycle.COMPLETED,
        StageLifecycle.COMPLETED_WITH_WARNINGS,
        StageLifecycle.FAILED,
    ],
)
def test_stage_lifecycle_allows_each_terminal_outcome(lifecycle: StageLifecycle):
    adapter = RunEventAdapter()

    adapter.start()
    adapter.begin_stage(Stage.PREPARE)
    adapter.finish_stage(Stage.PREPARE, lifecycle)

    assert adapter.stage_history[Stage.PREPARE] is lifecycle


def test_stage_lifecycle_rejects_out_of_order_stages():
    adapter = RunEventAdapter()

    adapter.start()
    adapter.begin_stage(Stage.PREPARE)
    adapter.finish_stage(Stage.PREPARE, StageLifecycle.COMPLETED)

    with pytest.raises(ValueError, match="fixed user-facing order"):
        adapter.begin_stage(Stage.EVIDENCE)


def test_cancelled_run_retains_stage_history_and_never_exposes_results():
    adapter = RunEventAdapter()
    adapter.start()
    adapter.begin_stage(Stage.PREPARE)

    run = adapter.cancel()

    assert run.outcome is RunOutcome.CANCELLED
    assert run.results is None
    assert run.stage_history[Stage.PREPARE] is StageLifecycle.RUNNING
    assert run.events[-1].kind == "terminal"


def test_skipped_source_is_a_visible_limitation_not_empty_results():
    updates = _completed_updates()
    updates[1] = (
        "searcher",
        {"candidates": [], "logs": ["searcher: kaggle skipped - credentials not configured"]},
    )
    updates[2] = ("gather_evidence", {"candidates": []})
    updates[3] = ("evaluator", {"evaluations": [], "report": "Limited coverage"})

    run = RunEventAdapter().adapt(updates)

    assert run.outcome is RunOutcome.COMPLETED_WITH_WARNINGS
    assert run.results is not None
    assert any(event.kind == "limitation" for event in run.events)


def test_verified_requirement_checks_require_a_citation_but_unknown_checks_do_not():
    with pytest.raises(ValidationError, match="evidence citation"):
        RequirementCheck(requirement="English text", status="met")

    check = RequirementCheck(requirement="English text", status="unknown")

    assert check.citation is None
