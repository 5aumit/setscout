from __future__ import annotations

import asyncio
import json
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from huggingface_hub import hf_hub_download
from tenacity import retry, stop_after_attempt, wait_exponential

from setscout.tools.search import _has_kaggle_credentials

if TYPE_CHECKING:
    from setscout.models import DatasetCandidate


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
def _fetch_hf_card_sync(repo_id: str) -> str:
    path = hf_hub_download(repo_id=repo_id, repo_type="dataset", filename="README.md")
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def _metadata_parts(data: dict) -> list[str]:
    parts: list[str] = []
    for key in ("title", "subtitle", "description"):
        value = data.get(key)
        if value:
            parts.append(str(value))
    for item in data.get("resources") or []:
        fields = [item.get("name"), item.get("description"), item.get("schema")]
        resource_text = "\n".join(str(value) for value in fields if value)
        if resource_text:
            parts.append(resource_text)
    return parts


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
def _fetch_kaggle_card_sync(ref: str) -> str:
    if not _has_kaggle_credentials():
        return ""

    from kaggle.api.kaggle_api_extended import KaggleApi

    api = KaggleApi()
    api.authenticate()
    with tempfile.TemporaryDirectory() as tmp:
        api.dataset_metadata(ref, tmp)
        metadata_path = Path(tmp) / "dataset-metadata.json"
        if not metadata_path.exists():
            return ""
        data = json.loads(metadata_path.read_text(encoding="utf-8"))
    # Kaggle API nests title/subtitle/description under "info", not at the root.
    payload = data.get("info", data)
    text = "\n\n".join(_metadata_parts(payload))
    return text


def _fetch_card_sync(candidate: DatasetCandidate) -> str:
    meta = candidate.raw_metadata
    if candidate.source == "huggingface":
        repo_id = meta.get("repo_id")
        if not repo_id:
            return ""
        return _fetch_hf_card_sync(repo_id)
    if candidate.source == "kaggle":
        ref = meta.get("ref")
        if not ref:
            return ""
        return _fetch_kaggle_card_sync(ref)
    return ""


async def fetch_dataset_card(candidate: DatasetCandidate) -> str:
    try:
        return await asyncio.to_thread(_fetch_card_sync, candidate)
    except (Exception, SystemExit):
        return ""
