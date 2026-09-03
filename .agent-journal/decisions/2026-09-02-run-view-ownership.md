# Run View ownership and scope

## Decision

Treat the Run View as an **UNDERSTAND** subsystem. Keep the existing Run event contract as the
boundary between pipeline internals and the user-facing view. Do not decide its implementation
only as a UI cleanup task.

## Why

SetScout users need to understand the Search Brief, the ranked Results, the retrieved evidence,
and the limits of a Run. Choices about rank repair, evidence validity, and warnings change the
meaning and trustworthiness of Results. They also affect later Recall@k or nDCG evaluation for the
harness ship.

## Tradeoff

This requires a dedicated product-understanding session before finishing Issue #8. It avoids
polishing a view that could present unverified evidence or an application-repaired ranking as if it
were fully trustworthy.

## Reconsider when

Reconsider this ownership level after the Run contract and evidence policy are settled and the
implementation has focused tests. The renderer and styling can then be delegated, with a final
human review of the end-to-end Run flow.
