# SetScout architecture

## Pipeline

Four nodes, two LLM calls per query:

1. **Decomposer** — enriches form inputs into a `SearchSpec` (keywords, MeSH terms, sources, constraints). Uses Gemma 4 (`gemma-4-31b-it` by default). Rule-based fallback if the LLM fails.
2. **Searcher** — parallel async search across Hugging Face and Kaggle. No LLM. Returns up to `SETSCOUT_MAX_CANDIDATES` (default 8) candidates.
3. **Gather evidence** — parallel HTTP fetch of dataset cards (README / Kaggle metadata), trimmed to `SETSCOUT_BATCH_EXCERPT_CHARS` (default 20000) per card. No LLM.
4. **Evaluator** — single batch LLM call (`gemini-2.5-flash-lite` by default) over all candidates and card excerpts. Produces per-candidate requirement checks, issue findings, fit summaries, ranks, and a markdown report.

### Long-term (v2+, not yet implemented)

- Gather evidence will also fetch paper abstracts and community discussions
- A per-candidate RAG enrichment node will run between gather evidence and evaluator
- `EvidenceDoc.kind` already supports `"paper"` and `"discussion"` for this

## State

All nodes share `SetScoutState` (`graph/state.py`). User inputs live in `query`; pipeline outputs (`search_spec`, `candidates`, `evaluations`, `report`) are populated progressively. Nodes read from and write to state; the LLM is passed as a parameter, never imported as a global.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SETSCOUT_DECOMPOSER_MODEL` | `gemma-4-31b-it` | Decomposer LLM |
| `SETSCOUT_REPORT_MODEL` | `gemini-2.5-flash-lite` | Evaluator LLM |
| `SETSCOUT_MAX_CANDIDATES` | `8` | Max datasets returned by searcher |
| `SETSCOUT_BATCH_EXCERPT_CHARS` | `20000` | Max chars per dataset card excerpt |
| `SETSCOUT_ENRICHMENT_CONCURRENCY` | `2` | Parallel fetch concurrency |
| `SETSCOUT_TRUNCATE_AT` | `12000` | Prompt truncation threshold |
| `SETSCOUT_HEAD_CHARS` | `8000` | Head chars when truncating |
| `SETSCOUT_TAIL_CHARS` | `4000` | Tail chars when truncating |

Optional integrations (set in `.env` when needed):

| Variable | Description |
|----------|-------------|
| `KAGGLE_USERNAME` / `KAGGLE_KEY` | Enables Kaggle search |
| `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_BASE_URL` | Enables Langfuse tracing |

## Project layout

```
setscout/
  graph/          # LangGraph state, builder, and node implementations
  models/         # Pydantic schemas (UserQuery, SearchSpec, DatasetCandidate, …)
  tools/          # Search, document fetch, async helpers
  pipeline.py     # run_pipeline() entry point
scripts/          # CLI smoke runner
```

## Conventions

- All agents are LangGraph nodes in `graph/nodes/`
- External API wrappers go in `tools/`
- Async where possible, especially in the searcher and gather-evidence nodes
- Never hardcode API keys; use environment variables
