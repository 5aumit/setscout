# SetScout

> **WIP:** This project is still under active development. APIs, behavior, and docs may change.

Agentic dataset discovery and evaluation for ML researchers. Describe what you need in natural language; a LangGraph pipeline searches Hugging Face and Kaggle, gathers dataset-card evidence, scores candidates, and produces a structured report.

For in-depth documentation, see [deepwiki.com/5aumit/setscout](https://deepwiki.com/5aumit/setscout).

## Setup

```bash
conda env create -f environment.yml
conda activate setscout
pip install -e ".[dev]"
```

Create a repo-root `.env` with your `GEMINI_API_KEY`.

## Request fields

**Required:** `purpose`, `domain`, `data_type`

**Optional:** `requirements` (free-text constraints), `additional_notes`, `exclude_datasets` (comma-separated names or list)

## Run

**Python API:**

```python
from setscout import run_pipeline

result = run_pipeline({
    "purpose": "benchmark sentiment classifiers",
    "domain": "natural language processing",
    "data_type": "text datasets",
    "requirements": "English, labeled, at least 1000 examples",
    "exclude_datasets": "IMDB",
})
print(result["report"])
```

Pass `api_key="..."` to override `GEMINI_API_KEY` from the environment (e.g. user-supplied key at runtime).

**Smoke run** (timestamped logs under `logs/`):

```bash
python -m scripts.run_pipeline_once
```

`app.py` is the Hugging Face Spaces entry point; it re-exports `run_pipeline` for deployment.

## Architecture

See [setscout/README.md](setscout/README.md) for pipeline design, configuration, and project layout.
