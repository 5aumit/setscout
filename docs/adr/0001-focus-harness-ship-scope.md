# ADR 0001: Focus the Next Planning Pass on Harness Ship Scope

Date: 2026-07-20

## Status

Accepted

## Context

SetScout already has a working LangGraph-based dataset discovery pipeline. The
next useful planning step is to turn the immediate shipping target into a spec
and local markdown tickets, without expanding the work into a larger redesign or
full evaluation program.

## Decision

Plan and ticket the harness ship first.

The harness ship is limited to:

- a stable public demo or Hugging Face Space;
- a README that makes the project easy to understand and run;
- 20 labeled queries;
- ranking metrics such as recall@k or nDCG-style scoring;
- a light report rubric;
- one baseline ablation comparing the full pipeline with a single-shot LLM pick
  from raw search results.

Do not expand the harness ship to include trained rankers or judges, a broad
ablation suite, the full 50-query evaluation set, or major graph redesigns.

## Consequences

The next planning flow should focus on the harness ship only:

1. refine any remaining domain language with `/grill-with-docs`;
2. write a harness-ship spec with `/to-spec`;
3. split it into local markdown tickets with `/to-tickets`;
4. implement one ticket per fresh context.

Larger evaluation work can follow after the harness ship is complete.
