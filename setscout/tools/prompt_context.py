from __future__ import annotations

import os

TRUNCATION_PREAMBLE = """\
Note: The dataset documentation below was truncated because it exceeded the size limit.
[HEAD] is the beginning of the document; [TAIL] is the end. The middle section was omitted.
Information may only appear in the omitted section; use null/empty if a field cannot be confirmed.\
"""


def _truncate_at() -> int:
    return int(os.environ.get("SETSCOUT_TRUNCATE_AT", "12000"))


def _head_chars() -> int:
    return int(os.environ.get("SETSCOUT_HEAD_CHARS", "8000"))


def _tail_chars() -> int:
    return int(os.environ.get("SETSCOUT_TAIL_CHARS", "4000"))


def preamble(truncated: bool) -> str:
    return f"{TRUNCATION_PREAMBLE}\n\n" if truncated else ""


def format_batch_excerpt(text: str, max_chars: int) -> str:
    """Return a head-only excerpt of text for use in batch prompts."""
    if not text:
        return ""
    return text[:max_chars]


def format_card_context(card_text: str) -> tuple[str, bool]:
    if not card_text:
        return "", False
    if len(card_text) <= _truncate_at():
        return card_text, False
    head = card_text[: _head_chars()]
    tail = card_text[-_tail_chars() :]
    formatted = (
        "[HEAD - start of dataset documentation; middle section omitted]\n"
        f"{head}\n"
        "[TAIL - end of dataset documentation]\n"
        f"{tail}"
    )
    return formatted, True
