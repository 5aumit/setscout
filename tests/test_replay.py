from __future__ import annotations

from setscout.replay import load_practice_run
from setscout.runs import RunOutcome, Stage, StageLifecycle


def test_saved_practice_run_is_a_complete_successful_run():
    replay = load_practice_run()

    assert replay.version == 1
    assert replay.run.outcome is RunOutcome.COMPLETED
    assert replay.run.results is not None
    assert replay.run.stage_history == {stage: StageLifecycle.COMPLETED for stage in Stage}
    assert [evaluation.rank for evaluation in replay.run.results.evaluations] == [1, 2]


def test_saved_practice_data_contains_only_the_public_safe_contract():
    replay = load_practice_run()
    serialized = replay.model_dump_json().lower()

    for forbidden in ("api_key", "gemini", "prompt", "traceback", "stack trace", "authorization"):
        assert forbidden not in serialized
