# 5stack feedback

Project-local observations about 5stack behavior. This is an inbox and history, not durable project truth.

## Entry format

### FB-YYYYMMDD-NNN

- Date: YYYY-MM-DD
- Source: implicit | explicit | retrospective
- Signal: positive | negative | mixed
- 5stack: commit or version when available
- Status: unreviewed | addressed | usage issue | project-specific | declined

**Observed behavior:**

**Expected or preferred behavior:**

**Context:**

### FB-20260902-001

- Date: 2026-09-02
- Source: explicit
- Signal: mixed
- 5stack: 157c934
- Status: addressed

**Observed behavior:**

For a requested 30-minute meaningful-progress task, the first recommendation was a low-priority maintenance or defensive suggestion, described by the user as a gitignore fix. It did not feel like worthwhile use of the available time.

**Expected or preferred behavior:**

Prioritize a concrete product-correctness task with direct impact on SetScout's core output. The follow-up recommendation to reject silently corrected invalid evaluator ranks was a better use of the time, though its intended behavior still needs discussion before implementation.

**Context:**

SetScout task selection. The user requested one small implementation task for roughly 30 minutes and explicitly deprioritized cleanup and repository hygiene. The improved candidate was preventing malformed LLM rankings from being silently renumbered before presenting results or measuring ranking quality.

### FB-20260902-002

- Date: 2026-09-02
- Source: retrospective
- Signal: negative
- 5stack: 157c934
- Status: addressed

**Observed behavior:**

The initial Git audit handoff mixed active work, optional housekeeping, Git internals, and
recommended next actions. The user explicitly invoked `wait-what` because it did not explain the
immediate situation clearly.

**Expected or preferred behavior:**

For a repository-status request, lead with the immediate decision and separate it from optional
cleanup. Use the project vocabulary, define only necessary terms, and state clearly when active
uncommitted work means that no deletion should happen yet.

**Context:**

SetScout Git cleanup audit across the main checkout, linked worktrees, and GitHub. A simpler
re-pitch made the next action clear: preserve active work first, then clean caches and retire the
completed review worktree.
