from __future__ import annotations

from setscout.presentation import render_run_view
from setscout.replay import load_practice_run
from setscout.runs import RunOutcome, RunRecord, SearchBrief, Stage, StageLifecycle


def test_run_view_renders_a_search_brief_completed_stage_history_summary_and_ranked_results():
    replay = load_practice_run()

    markup = render_run_view(replay.run, replay.search_brief)

    assert "Search Brief" in markup
    assert replay.search_brief.purpose in markup
    assert "Run summary" in markup
    assert "Completed" in markup
    assert "Prepare search brief" in markup
    assert "Rank 1" in markup
    assert replay.run.results.evaluations[0].fit_summary in markup
    assert "Show all 8 Results" in markup


def test_run_view_accepts_the_run_contract_without_a_replay_source_dependency():
    replay = load_practice_run()
    brief = SearchBrief(
        purpose="Compare annotations for product-review sentiment.",
        domain="Natural language processing",
        data_type="Labeled text",
        requirements="English and a permissive license.",
    )

    markup = render_run_view(replay.run, brief)

    assert brief.purpose in markup
    assert "Rank 1" in markup


def test_run_view_labels_a_cancelled_run_without_claiming_it_completed():
    brief = SearchBrief(
        purpose="Compare annotations for product-review sentiment.",
        domain="Natural language processing",
        data_type="Labeled text",
    )
    run = RunRecord(
        events=[],
        outcome=RunOutcome.CANCELLED,
        stage_history={stage: StageLifecycle.WAITING for stage in Stage},
    )

    markup = render_run_view(run, brief)

    assert "Cancelled" in markup
    assert "completed all four stages" not in markup.lower()
