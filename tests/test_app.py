from __future__ import annotations

from app import _run


def test_live_run_errors_are_returned_to_the_markdown_output_only():
    updates = next(_run(None, None, None, None, None, None, None))

    assert isinstance(updates, tuple)
    markdown, ledger = updates
    assert markdown.value == "**Error:** Gemini API key is required."
    assert markdown.visible is True
    assert ledger.visible is False
