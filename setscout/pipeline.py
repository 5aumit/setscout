from __future__ import annotations

import os
from typing import Any

from setscout.graph import build_setscout_graph
from setscout.graph.state import SetScoutState
from setscout.models import UserQuery


def user_query_from_dict(d: dict[str, Any]) -> UserQuery:
    exclude = d.get("exclude_datasets") or []
    if isinstance(exclude, str):
        exclude = [x.strip() for x in exclude.split(",") if x.strip()]
    return UserQuery(
        purpose=str(d["purpose"]).strip(),
        domain=str(d["domain"]).strip(),
        data_type=str(d["data_type"]).strip(),
        requirements=(str(d["requirements"]).strip() or None) if d.get("requirements") else None,
        additional_notes=(
            (str(d["additional_notes"]).strip() or None) if d.get("additional_notes") else None
        ),
        exclude_datasets=[str(x).strip() for x in exclude if str(x).strip()],
    )


def run_pipeline(
    request: dict[str, Any],
    *,
    api_key: str | None = None,
) -> SetScoutState:
    q = user_query_from_dict(request)
    if not all([q.purpose, q.domain, q.data_type]):
        raise ValueError("purpose, domain, and data_type are required")

    key = api_key if api_key is not None else os.environ.get("GEMINI_API_KEY") or None
    app = build_setscout_graph(key)
    initial: SetScoutState = {"query": q, "logs": []}
    return app.invoke(initial)
