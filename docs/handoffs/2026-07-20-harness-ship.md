# Handoff: SetScout harness ship → portfolio ship

**Date:** 2026-07-20  
**Source session:** portfolio / AI-eng project grilling (stateless `/grill-me`, not in-repo)  
**Target repo:** `/mnt/d/DTSC/setscout`  
**Next session focus:** Capture decisions in-repo, then spec/tickets for harness ship (not greenfield; not a new project)

---

## Situation

User grilled whether to start more AI-eng portfolio projects. **Decision: no.** Continue SetScout until it clears a defined ship ladder. KV-cache transfer between LLMs is an optional side research idea only.

SetScout already exists (agentic dataset discovery for ML researchers; LangGraph; HF/Kaggle; HF Spaces entry via `app.py`). Job-search docs do **not** list SetScout; GitHub: https://github.com/5aumit/setscout

---

## Locked plan

### Goals
- ~60% portfolio hire signal, ~40% skill growth
- Role bar: Applied LLM eng + Modeling eng (equal); lesser ML platform/infra; not full-stack+AI-primary
- Compute: API-only for applied path; Colab or local RTX 4060 (8GB) only if training is justified
- **Do not train a model for its own sake.** Modeling (e.g. reranker/judge) only if evals show ranking/fit quality is the bottleneck and heuristics plateau

### Flagship
- **SetScout** — must be openable/usable as a public demo (HF Space path already sketched)
- Medical imaging is resume moat (DeepTek) but **not** the forced vertical for this project (demo/usability constraint)
- Floki / cache-policy agent / compression / speech stay as existing resume items; **do not start Project N** for portfolio anxiety
- Do **not** merge Floki into SetScout for first ship

### Eval design (portfolio-relevant)
- Ground truth **D:** primary = acceptable dataset IDs per query; secondary = light report rubric (no hallucinated IDs, citations/grounding)
- Label sourcing **D (hybrid, A-heavy):** real past ML needs + some public starter tasks; not “wait for production logs” as the exit plan
- Metrics: recall@k / nDCG-style ranking + subset report rubric

### Ship ladder
1. **Harness ship (first):**
   - Stable public demo/Space + README
   - **20** labeled queries (v0 harness)
   - recall@k + light report rubric
   - **One** baseline ablation: full pipeline vs single-shot LLM pick from raw search results
2. **Portfolio ship (next / exit for “AI eng portfolio complete”):**
   - Grow to ~**50** quality, diverse labeled queries
   - **Solid** ablations (add: no report-grounding / allow hallucinated IDs; search-only heuristic rank without agent refinement)
   - Trained model only if justified by metrics after this

### First-ship non-goals (aggressive cut)
- No trained ranker/judge
- No solid (multi) ablations yet
- No major LangGraph redesign / new major agent nodes
- No Floki integration
- No medical-specialized mode
- No KV-cache work
- Do not expand first ship to the full 50-query + solid-ablation bar

### Sequencing note
- Ablations: start with minimal (**A**), deepen to solid (**B**) at portfolio ship — “ship first,” but harness ship still includes the **single** baseline ablation above

---

## Candidate background (context only; not SetScout scope)

Profile/resume live under job-search docs (Windows path used in grill session): `/mnt/d/tech_stuff/jobs/docs/`  
Strongest domain: medical imaging AI / CV; also MLOps, agents (Floki, Langfuse), speech research. Targeting Applied/LLM/Agentic/ML eng; F-1, sponsorship later; grad ~2027-05.

Use for resume framing later; **do not** pivot SetScout into clinical PHI workflows for the demo.

---

## What the next agent should do

1. Open session with cwd `/mnt/d/DTSC/setscout` and this handoff.
2. Skim existing SetScout code + `docs/agents/*` + README so tickets match reality.
3. Optionally `/grill-with-docs` to persist glossary/decisions into `CONTEXT.md` / ADRs (grill-me left no in-repo paper trail).
4. `/to-spec` for **harness ship only** (not the whole portfolio ladder in one mega-spec unless natural).
5. `/to-tickets` with blocking edges; work blockers-first.
6. `/implement` **per ticket in fresh contexts** (TDD + code-review per skill flow).

Do **not** implement the whole ladder from a home-directory or this handoff-only context. Do **not** start a new portfolio project.

---

## Suggested skills

| Order | Skill | Why |
|---|---|---|
| 1 | `/grill-with-docs` | File locked decisions into SetScout `CONTEXT.md`/ADRs; align domain language with existing `docs/agents/domain.md` |
| 2 | `/to-spec` | Turn harness-ship bar into a buildable spec |
| 3 | `/to-tickets` | Tracer-bullet tickets with blocking edges (labels → harness → baseline ablation → demo/README) |
| 4 | `/implement` (+ internal `/tdd`, `/code-review`) | One ticket per fresh session |
| — | `/domain-modeling` | If “query”, “candidate”, “fit”, “report” are overloaded while writing CONTEXT/spec |
| — | `/prototype` | Only if golden-set schema or metric definition needs a throwaway spike |
| — | `/handoff` | Again when context fills before `/to-tickets` completes |
| Avoid for now | `/wayfinder` | Path is already clear |
| Avoid for now | `/triage` | These are planned tickets, not raw incoming issues |
| Side only | KV-cache research | Explicitly out of SetScout first ship |

---

## In-repo copy

Canonical working copy for the SetScout session:

`docs/handoffs/2026-07-20-harness-ship.md`
