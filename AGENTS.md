# Repository Guidelines

## Project Overview

SetScout is an agentic dataset discovery and evaluation tool for ML researchers. Users describe needs in natural language; a LangGraph pipeline searches Hugging Face and Kaggle, gathers dataset-card evidence, scores candidates, and returns a structured markdown report.

The project is **WIP** — APIs, behavior, and docs may change.

## Architecture & Data Flow

Four sequential LangGraph nodes, **two LLM calls** per query:

```
UserQuery → decomposer → searcher → gather_evidence → evaluator → report
```

| Node | LLM? | Role |
|------|------|------|
| `decomposer` | Yes (`gemma-4-31b-it`) | Expand form inputs into `SearchSpec` (keywords, sources, constraints). Rule-based fallback on failure. |
| `searcher` | No | Async HF + Kaggle search; interleave, exclude, cap at `SETSCOUT_MAX_CANDIDATES`. |
| `gather_evidence` | No | Parallel fetch of dataset cards; trim excerpts. |
| `evaluator` | Yes (`gemini-2.5-flash-lite`) | Single batch LLM over candidates + excerpts → ranks, checks, markdown report. Fallback report on failure. |

Shared state is `SetScoutState` (`setscout/graph/state.py`): `query`, `search_spec`, `candidates`, `evaluations`, `report`, plus append-only `logs`.

**Patterns:**
- Nodes return partial state dicts; logs via `log("...")` → `{"logs": [...]}` (`Annotated[list[str], add]`).
- LLMs are injected with `functools.partial` in `build_setscout_graph` — never imported as globals.
- Sync LangGraph nodes call async tools through `setscout.tools.async_utils.run_async`.
- External APIs live under `setscout/tools/`; graph orchestration under `setscout/graph/`.

Long-term (not implemented): paper/discussion evidence and a per-candidate enrichment node. `EvidenceDoc.kind` already allows `"paper"` / `"discussion"`.

## Key Directories

| Path | Purpose |
|------|---------|
| `setscout/graph/` | LangGraph builder, state, nodes |
| `setscout/graph/nodes/` | `decomposer`, `searcher`, `gather_evidence`, `evaluator`, `llm` |
| `setscout/models/` | Pydantic schemas (`UserQuery`, `SearchSpec`, `DatasetCandidate`, …) |
| `setscout/tools/` | Search, document fetch, enrichment concurrency, prompt truncation, async bridge |
| `setscout/pipeline.py` | `run_pipeline()` public entry |
| `scripts/` | CLI smoke runner |
| `tests/` | Pytest suite |
| `app.py` | Gradio / Hugging Face Spaces UI |

## Development Commands

```bash
# Env + install
conda env create -f environment.yml
conda activate setscout
pip install -e ".[dev]"

# Lint
ruff check .

# Tests
python -m pytest

# Smoke run (writes logs/pipeline-<timestamp>.log)
python -m scripts.run_pipeline_once

# Local Gradio UI
python app.py
```

Python API:

```python
from setscout import run_pipeline

result = run_pipeline({
    "purpose": "...",
    "domain": "...",
    "data_type": "...",
    "requirements": "...",
    "additional_notes": "...",
    "exclude_datasets": "IMDB",
}, api_key=None)
print(result["report"])
```

## Important Files

| File | Why it matters |
|------|----------------|
| `setscout/pipeline.py` | Validates request, requires Gemini key, invokes graph, flushes traces |
| `setscout/graph/builder.py` | Wires node graph and model env overrides |
| `setscout/graph/state.py` | Shared `SetScoutState` |
| `setscout/models/schemas.py` | Contract between nodes |
| `setscout/tools/search.py` | HF/Kaggle search + interleave |
| `setscout/tools/prompt_context.py` | Card truncation / batch excerpts |
| `setscout/tracing.py` | Optional Langfuse callbacks |
| `app.py` | Spaces entry (`sdk: gradio`, `app_file: app.py` in README frontmatter) |
| `scripts/run_pipeline_once.py` | Fixed `REQUEST` smoke path |
| `pyproject.toml` | Deps, Ruff, Pytest config |
| `environment.yml` | Conda env (Python 3.11) |

## Runtime/Tooling Preferences

- **Runtime:** Python **≥3.11** (Conda pin: 3.11).
- **Package managers:** Conda for the env; **pip** editable install for the package.
- **Build:** Hatchling (`pyproject.toml`).
- **LLM provider:** Google Gemini via `langchain-google-genai`; required `GEMINI_API_KEY` (or `api_key=` override).
- **Optional:** `KAGGLE_USERNAME` / `KAGGLE_KEY` (Kaggle soft-fails without them); `LANGFUSE_*` for tracing.
- **Tunables:** `SETSCOUT_DECOMPOSER_MODEL`, `SETSCOUT_REPORT_MODEL`, `SETSCOUT_MAX_CANDIDATES`, `SETSCOUT_BATCH_EXCERPT_CHARS`, `SETSCOUT_ENRICHMENT_CONCURRENCY`, `SETSCOUT_TRUNCATE_AT`, `SETSCOUT_HEAD_CHARS`, `SETSCOUT_TAIL_CHARS`.
- **No CI workflows** in-repo currently; no mypy/black — use Ruff.
- Put secrets in repo-root `.env` (not committed).

## Code Conventions & Common Patterns

- **Python:** `from __future__ import annotations`; type hints; Pydantic models for structured I/O.
- **Naming:** `snake_case` functions/modules; PascalCase models; `_private` helpers.
- **Lint:** Ruff (`E`, `F`, `I`, `UP`), line length **100**, target **py311**.
- **Async:** Prefer async in searcher/gather-evidence tooling; bridge with `run_async` from sync nodes.
- **Errors:** Node-level try/except with deterministic fallbacks (decomposer/evaluator) and log messages; do not hard-fail the whole graph when an LLM call fails.
- **Config:** Environment variables only for secrets and tunables — never hardcode API keys.
- **DI / state:** Pass `llm` into nodes; mutate via returned state patches, not module globals.
- **New agents:** Add as LangGraph nodes under `graph/nodes/`; wrap external APIs in `tools/`.

## Testing & QA

- **Framework:** Pytest + `pytest-asyncio` (`asyncio_mode = auto`, `testpaths = ["tests"]`).
- **Run:** `python -m pytest`
- **Style:** Unit tests with `unittest.mock` / `monkeypatch`; no coverage gate configured.
- **Current suite:** `tests/test_pipeline.py`, `test_decomposer.py`, `test_search.py`, `test_prompt_context.py`, plus older files (`test_extractor.py`, `test_scorer.py`, `test_merge_enrichment.py`, `test_constraints.py`).

**Agent caveat:** Several tests still import removed modules (`graph/nodes/extractor`, `scorer`, `merge_enrichment`, `tools/constraints`) that exist only as `__pycache__` artifacts. The live pipeline is the four-node graph above. Prefer updating or deleting stale tests when touching architecture; do not resurrect old nodes unless explicitly requested.

## Agent skills

### Issue tracker

Issues and specs live in this repository's GitHub Issues. See `docs/agents/issue-tracker.md`.

### Triage labels

Five canonical roles map to GitHub issue labels. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout: root `CONTEXT.md` and `docs/adr/`. See `docs/agents/domain.md`.
