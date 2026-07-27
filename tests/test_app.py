from __future__ import annotations

from app import _replay_run, _run, _test_run_enabled
from setscout.models import CandidateEvaluation, DatasetCandidate
from setscout.pipeline import stream_pipeline


def test_live_run_errors_are_returned_to_the_markdown_output_only():
    updates = next(_run(None, None, None, None, None, None, None))

    assert isinstance(updates, tuple)
    form, markdown, run_view = updates
    assert form.visible is True
    assert markdown.value == "**Error:** Gemini API key is required."
    assert markdown.visible is True
    assert run_view.visible is False


def test_live_run_hides_the_form_and_streams_run_view_updates(monkeypatch):
    candidate = DatasetCandidate(
        id="reviews",
        name="Product reviews",
        source="huggingface",
        url="https://example.com/reviews",
    )
    evaluation = CandidateEvaluation(
        candidate_id=candidate.id,
        rank=1,
        fit_summary="A strong fit for short sentiment classification.",
    )
    updates = iter(
        [
            ("decomposer", {"search_spec": object()}),
            ("searcher", {"candidates": [candidate]}),
            ("gather_evidence", {"candidates": [candidate]}),
            ("evaluator", {"evaluations": [evaluation], "report": "One strong match."}),
        ]
    )
    monkeypatch.setattr("setscout.pipeline.stream_pipeline", lambda *args, **kwargs: updates)

    snapshots = list(
        _run(
            "test-key",
            "Classify product-review sentiment",
            "NLP",
            "Labeled text",
            "English",
            None,
            None,
        )
    )

    first_form, first_markdown, first_view = snapshots[0]
    assert first_form.visible is False
    assert first_markdown.visible is False
    assert "Classify product-review sentiment" in first_view.value
    assert "Search Brief" in first_view.value
    assert "Running" in first_view.value
    assert "Ranked Results" not in first_view.value

    final_form, final_markdown, final_view = snapshots[-1]
    assert final_form.visible is False
    assert final_markdown.visible is False
    assert "Ranked Results" in final_view.value
    assert "Product reviews" in final_view.value
    assert "A strong fit for short sentiment classification." in final_view.value
    assert "1 dataset candidates" in snapshots[3][2].value


def test_live_run_failure_keeps_the_form_available_for_a_retry(monkeypatch):
    def _failing_stream(*args, **kwargs):
        raise RuntimeError("provider unavailable")
        yield

    monkeypatch.setattr("setscout.pipeline.stream_pipeline", _failing_stream)

    updates = list(
        _run("test-key", "Classify reviews", "NLP", "Labeled text", None, None, None)
    )

    form, markdown, run_view = updates[-1]
    assert form.visible is True
    assert (
        markdown.value
        == "**Unable to complete this Run.** Check your Gemini API key and try again."
    )
    assert run_view.visible is False


def test_pipeline_stream_yields_each_completed_stage_patch_and_flushes_traces(monkeypatch):
    stream_calls = []
    flushed = []

    class Graph:
        def stream(self, initial, *, stream_mode, config):
            stream_calls.append((initial, stream_mode, config))
            return iter(
                [
                    {"decomposer": {"search_spec": object()}},
                    {"searcher": {"candidates": []}},
                ]
            )

    monkeypatch.setattr("setscout.pipeline.build_setscout_graph", lambda key: Graph())
    monkeypatch.setattr("setscout.pipeline.flush_traces", lambda: flushed.append(True))

    updates = list(
        stream_pipeline(
            {"purpose": "classify reviews", "domain": "NLP", "data_type": "labeled text"},
            api_key="test-key",
        )
    )

    assert [name for name, _ in updates] == ["decomposer", "searcher"]
    assert stream_calls[0][1] == "updates"
    assert flushed == [True]


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
