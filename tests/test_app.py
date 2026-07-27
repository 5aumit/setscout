from __future__ import annotations

from app import _replay_run, _run, _test_run_enabled


def test_live_run_errors_are_returned_to_the_markdown_output_only():
    updates = next(_run(None, None, None, None, None, None, None))

    assert isinstance(updates, tuple)
    markdown, run_view = updates
    assert markdown.value == "**Error:** Gemini API key is required."
    assert markdown.visible is True
    assert run_view.visible is False


def test_test_run_requires_an_explicit_environment_flag(monkeypatch):
    monkeypatch.delenv("SETSCOUT_ENABLE_TEST_RUN", raising=False)
    assert _test_run_enabled() is False

    monkeypatch.setenv("SETSCOUT_ENABLE_TEST_RUN", "1")
    assert _test_run_enabled() is True


def test_offline_replay_advances_then_reveals_results_only_at_completion(monkeypatch):
    monkeypatch.setattr("app.sleep", lambda _: None)

    updates = list(_replay_run())

    assert len(updates) > 4
    assert "Run Activity" in updates[1][1].value
    assert "Ranked Results" not in updates[-2][1].value
    assert "Ranked Results" in updates[-1][1].value
