from __future__ import annotations

from setscout.presentation import render_ledger
from setscout.replay import load_practice_run
from setscout.runs import RunOutcome, RunRecord, SearchBrief, Stage, StageLifecycle


def test_ledger_renders_a_search_brief_completed_stage_history_summary_and_ranked_results():
    replay = load_practice_run()

    markup = render_ledger(replay.run, replay.search_brief)

    assert "Search Brief" in markup
    assert replay.search_brief.purpose in markup
    assert "Run Summary" in markup
    assert "Completed" in markup
    assert "01" in markup
    assert "Prepare the Search Brief" in markup
    assert "Rank 1" in markup
    assert replay.run.results.evaluations[0].fit_summary in markup


def test_ledger_accepts_the_run_contract_without_a_replay_source_dependency():
    replay = load_practice_run()
    brief = SearchBrief(
        purpose="Compare annotations for product-review sentiment.",
        domain="Natural language processing",
        data_type="Labeled text",
        requirements="English and a permissive license.",
    )

    markup = render_ledger(replay.run, brief)

    assert brief.purpose in markup
    assert "Rank 1" in markup


def test_ledger_labels_a_cancelled_run_without_claiming_it_completed():
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

    markup = render_ledger(run, brief)

    assert "Cancelled Run" in markup
    assert "Completed all four stages." not in markup
