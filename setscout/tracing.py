from __future__ import annotations

import os


def _langfuse_enabled() -> bool:
    return bool(os.environ.get("LANGFUSE_PUBLIC_KEY") and os.environ.get("LANGFUSE_SECRET_KEY"))


def invoke_config() -> dict:
    if not _langfuse_enabled():
        return {}
    from langfuse.langchain import CallbackHandler

    return {
        "callbacks": [CallbackHandler()],
        "metadata": {
            "langfuse_trace_name": "setscout-pipeline",
            "langfuse_tags": ["setscout"],
        },
    }


def flush_traces() -> None:
    if _langfuse_enabled():
        from langfuse import get_client

        get_client().flush()
