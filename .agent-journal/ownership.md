# Ownership

## Run View

- Recommended ownership: **UNDERSTAND** for the user-facing Result meaning; **DELEGATE** for the
  implementation after those choices are settled; **REVIEW** only the completed end-to-end flow.
- The manual conceptual review should follow: Search Brief -> retrieved evidence -> evaluation ->
  ranked Results -> warnings.
- Saumit needs to decide:
  - when a ranked Result is trustworthy enough to show;
  - what `completed_with_warnings` communicates about a Run;
  - whether invalid evaluator ranks fail the evaluation or are repaired and disclosed;
  - what evidence can support a Requirement Check;
  - whether `known_issues` is sufficient for a candidate-specific downside.
- Delegate after those decisions: the presentation renderer, safe HTTP(S) links, evidence matching,
  tests, replay data, and any Run-contract change needed to carry the chosen information.
- Review after implementation: whether the Run View distinguishes what SetScout knows, what it does
  not know, and what it repaired. Detailed HTML and CSS review is not required.
- Status: deferred for a dedicated understanding session. The pending Issue #8 work is not ready
  to commit as complete.
