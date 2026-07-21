from __future__ import annotations

import pytest

from setscout.models import DatasetCandidate
from setscout.tools import search
from setscout.tools.search import _interleave_by_source


def _candidate(source: str, index: int) -> DatasetCandidate:
    return DatasetCandidate(
        id=f"{source}-{index}",
        source=source,
        name=f"{source} {index}",
        url=f"https://example.com/{source}/{index}",
    )


def test_interleave_preserves_source_priority_without_starving_later_sources():
    results = {
        "huggingface": [_candidate("huggingface", 1), _candidate("huggingface", 2)],
        "kaggle": [_candidate("kaggle", 1), _candidate("kaggle", 2)],
    }

    interleaved = _interleave_by_source(results, ["huggingface", "kaggle"])

    assert [candidate.id for candidate in interleaved] == [
        "huggingface-1",
        "kaggle-1",
        "huggingface-2",
        "kaggle-2",
    ]


def test_kaggle_search_soft_fails_without_credentials(monkeypatch, tmp_path):
    monkeypatch.delenv("KAGGLE_API_TOKEN", raising=False)
    monkeypatch.delenv("KAGGLE_USERNAME", raising=False)
    monkeypatch.delenv("KAGGLE_KEY", raising=False)
    monkeypatch.setenv("KAGGLE_CONFIG_DIR", str(tmp_path))

    spec = search.SearchSpec(
        expanded_keywords=["sentiment"],
        prioritized_sources=["kaggle"],
    )

    assert search._search_kaggle_sync(spec, limit=5) == []


@pytest.mark.asyncio
async def test_search_all_sources_logs_kaggle_system_exit(monkeypatch):
    monkeypatch.setenv("KAGGLE_USERNAME", "user")
    monkeypatch.setenv("KAGGLE_KEY", "key")

    async def fake_huggingface(spec):
        return [_candidate("huggingface", 1)]

    async def fake_kaggle(spec):
        raise SystemExit(1)

    monkeypatch.setattr(search, "search_huggingface", fake_huggingface)
    monkeypatch.setattr(search, "search_kaggle", fake_kaggle)

    spec = search.SearchSpec(
        expanded_keywords=["sentiment"],
        prioritized_sources=["huggingface", "kaggle"],
    )

    candidates, logs = await search.search_all_sources(spec)

    assert [candidate.id for candidate in candidates] == ["huggingface-1"]
    assert "searcher: kaggle failed - SystemExit: 1" in logs
