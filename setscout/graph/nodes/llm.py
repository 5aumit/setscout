from __future__ import annotations

import os

from langchain_google_genai import ChatGoogleGenerativeAI

DEFAULT_DECOMPOSER_MODEL = "gemma-4-31b-it"
DEFAULT_REPORT_MODEL = "gemini-2.5-flash-lite"


def make_llm(api_key: str, *, model: str | None = None):
    return ChatGoogleGenerativeAI(
        model=model or os.environ.get("SETSCOUT_LLM_MODEL", DEFAULT_REPORT_MODEL),
        google_api_key=api_key,
        temperature=0.2,
    )
