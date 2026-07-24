# SetScout Context

SetScout is an agentic dataset discovery and evaluation tool for ML researchers.
Users describe dataset needs in natural language; the pipeline searches Hugging
Face and Kaggle, gathers dataset-card evidence, scores candidates, and returns a
structured markdown report.

## Current Focus

The next planning flow should focus on the harness ship only:

1. refine any remaining domain language with `/grill-with-docs`;
2. write a harness-ship spec with `/to-spec`;
3. split it into local markdown tickets with `/to-tickets`;
4. implement one ticket per fresh context.

## Ship Ladder

### Harness Ship

This is the immediate target.

- Stable public demo or Hugging Face Space.
- README that makes the project easy to understand and run.
- 20 labeled queries for a v0 evaluation harness.
- Recall@k or nDCG-style ranking metrics.
- A light report rubric, including checks for hallucinated dataset IDs and
  citation or grounding quality.
- One baseline ablation: full pipeline versus a single-shot LLM pick from raw
  search results.

### Later Evaluation Work

After the harness ship:

- Grow the evaluation set to about 50 quality, diverse labeled queries.
- Add stronger ablations, such as:
  - no report grounding or allow hallucinated IDs;
  - search-only heuristic rank without agent refinement.
- Consider trained models only if evaluation shows ranking or fit quality is
  the bottleneck and simpler heuristics have plateaued.

## Harness Non-Goals

For the harness ship, do not add:

- A trained ranker or judge.
- A full multi-ablation suite.
- Major LangGraph redesigns or new major agent nodes.
- The full 50-query evaluation set.

## Evaluation Vocabulary

- **Labeled query**: a dataset discovery request with acceptable dataset IDs as
  ground truth.
- **Acceptable dataset ID**: a dataset identifier that should count as a good
  result for a labeled query.
- **Report rubric**: lightweight checks on the generated report, especially
  whether it avoids hallucinated dataset IDs and grounds claims in retrieved
  evidence.
- **Baseline ablation**: a comparison that removes the agentic pipeline and asks
  a single LLM call to choose from raw search results.

## Source Handoff

The next-step plan above was seeded from
`docs/handoffs/2026-07-20-harness-ship.md`.
