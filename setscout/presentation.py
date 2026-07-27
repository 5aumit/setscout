"""Custom Gradio Run View rendering from the public Run contract."""
# The renderer intentionally keeps HTML and theme-aware CSS readable in one module.
# ruff: noqa: E501

from __future__ import annotations

from html import escape

from setscout.models import CandidateEvaluation, RequirementCheck
from setscout.runs import (
    ActivityEvent,
    Count,
    ResultCandidate,
    RunOutcome,
    RunRecord,
    SearchBrief,
    Stage,
    StageLifecycle,
)

_STAGE_LABELS = {
    Stage.PREPARE: "Prepare search brief",
    Stage.SEARCH: "Search dataset sources",
    Stage.EVIDENCE: "Gather documentation evidence",
    Stage.EVALUATE: "Evaluate and rank candidates",
}

_CSS = """
<style>
.run-view { color:var(--body-text-color); font-family:var(--font); }
.run-view-shell {
  background:var(--block-background-fill); border:1px solid var(--border-color-primary);
  border-radius:var(--block-radius); box-shadow:var(--block-shadow); overflow:hidden;
}
.run-view-grid { display:grid; grid-template-columns:minmax(15rem,.85fr) minmax(24rem,1.45fr); }
.run-rail { background:var(--background-fill-secondary); padding:1.1rem; }
.run-main { border-left:1px solid var(--border-color-primary); padding:1.25rem; }
.run-kicker { color:var(--body-text-color-subdued); font-size:.74rem; font-weight:700; }
.run-kicker { letter-spacing:.06em; margin:0 0 .35rem; text-transform:uppercase; }
.run-title { color:var(--body-text-color); font-size:1.12rem; line-height:1.35; margin:0; }
.run-copy { color:var(--body-text-color-subdued); font-size:.88rem; line-height:1.5; margin:.45rem 0 0; }
.run-chips { display:flex; flex-wrap:wrap; gap:.45rem; margin-top:.75rem; }
.run-chip { background:var(--background-fill-primary); border:1px solid var(--border-color-primary); }
.run-chip { border-radius:999px; font-size:.76rem; padding:.28rem .55rem; }
.run-stage-list, .run-activity-list, .run-checks { list-style:none; margin:.9rem 0 0; padding:0; }
.run-stage { display:grid; gap:.55rem; grid-template-columns:1.5rem minmax(0,1fr) auto; padding:.75rem 0; }
.run-stage + .run-stage, .run-activity + .run-activity, .run-check + .run-check {
  border-top:1px solid var(--border-color-primary);
}
.run-marker { align-items:center; background:var(--background-fill-primary); border:1px solid var(--border-color-primary); }
.run-marker { border-radius:50%; color:var(--body-text-color-subdued); display:flex; font-size:.7rem; }
.run-marker { font-weight:700; height:1.4rem; justify-content:center; width:1.4rem; }
.run-stage strong { display:block; font-size:.88rem; }
.run-status { color:var(--body-text-color-subdued); font-size:.71rem; font-weight:650; white-space:nowrap; }
.run-stage.running .run-marker { background:var(--primary-100); border-color:var(--primary-500); }
.run-stage.running .run-marker { color:var(--primary-600); box-shadow:0 0 0 4px var(--primary-100); }
.run-stage.completed .run-marker { background:var(--primary-500); border-color:var(--primary-500); }
.run-stage.completed .run-marker { color:var(--button-primary-text-color); }
.run-stage.waiting { opacity:.58; }
.run-activity-panel, .run-summary { background:var(--background-fill-secondary); }
.run-activity-panel, .run-summary { border:1px solid var(--border-color-primary); padding:1rem; }
.run-activity-list { margin-top:.8rem; }
.run-activity { display:grid; gap:.6rem; grid-template-columns:1.25rem minmax(0,1fr); padding:.72rem 0; }
.run-activity-marker { align-items:center; background:var(--primary-500); border-radius:50%; }
.run-activity-marker { color:var(--button-primary-text-color); display:flex; font-size:.68rem; }
.run-activity-marker { font-weight:700; height:1.2rem; justify-content:center; width:1.2rem; }
.run-activity strong { display:block; font-size:.85rem; }
.run-terminal { border-left:3px solid var(--primary-500); margin-bottom:1rem; }
.run-details { margin-top:.5rem; }
.run-details summary, .run-result summary, .run-show-all summary { cursor:pointer; font-weight:650; }
.run-details summary, .run-result summary, .run-show-all summary { list-style:none; }
.run-details summary::-webkit-details-marker, .run-result summary::-webkit-details-marker { display:none; }
.run-show-all summary::-webkit-details-marker { display:none; }
.run-results-head { align-items:end; display:flex; gap:1rem; justify-content:space-between; }
.run-results-head { margin:1.2rem 0 .75rem; }
.run-result-list { display:grid; gap:.65rem; }
.run-result { background:var(--background-fill-secondary); border:1px solid var(--border-color-primary); }
.run-result { overflow:hidden; }
.run-result[open] { border-color:var(--primary-500); }
.run-result summary { display:grid; gap:.45rem; padding:.9rem 1rem; }
.run-result-top, .run-result-meta, .run-result-actions { align-items:center; display:flex; gap:.6rem; }
.run-result-top, .run-result-actions { justify-content:space-between; }
.run-result-meta { color:var(--body-text-color-subdued); font-size:.75rem; justify-content:flex-start; }
.run-rank { color:var(--primary-600); font-size:.72rem; font-weight:700; letter-spacing:.04em; }
.run-rank { text-transform:uppercase; }
.run-source { border-left:1px solid var(--border-color-primary); padding-left:.6rem; }
.run-result h3 { font-size:1rem; margin:0; }
.run-result-body { border-top:1px solid var(--border-color-primary); padding:.9rem 1rem 1rem; }
.run-check {
  display:grid; gap:.5rem;
  grid-template-columns:minmax(6rem,.75fr) minmax(7rem,.6fr)
    minmax(12rem,1.65fr);
  padding:.65rem 0;
}
.run-check strong, .run-check p { font-size:.8rem; margin:0; }
.run-check p { color:var(--body-text-color-subdued); }
.run-check-status { background:var(--background-fill-primary); border:1px solid var(--border-color-primary); }
.run-check-status { border-radius:999px; font-size:.7rem; font-weight:700; justify-self:start; }
.run-check-status { padding:.18rem .42rem; }
.run-check-status.met { background:var(--primary-100); border-color:transparent; color:var(--primary-600); }
.run-check-status.partial { background:var(--warning-100); border-color:transparent; color:var(--warning-700); }
.run-result-actions { border-top:1px solid var(--border-color-primary); margin-top:.7rem; padding-top:.7rem; }
.run-result-actions a { color:var(--link-text-color); font-size:.8rem; font-weight:650; white-space:nowrap; }
.run-show-all summary { border:1px solid var(--border-color-primary); padding:.75rem; text-align:center; }
.run-all-label { display:none; }
.run-main:has(.run-show-all[open]) .run-top-label { display:none; }
.run-main:has(.run-show-all[open]) .run-all-label { display:inline; }
@media (max-width:700px) {
  .run-view-grid { grid-template-columns:1fr; }
  .run-main { border-left:0; border-top:1px solid var(--border-color-primary); }
  .run-check { grid-template-columns:1fr; }
}
</style>
"""


def _stage_state(lifecycle: StageLifecycle) -> tuple[str, str, str]:
    labels = {
        StageLifecycle.WAITING: ("waiting", "Waiting", ""),
        StageLifecycle.RUNNING: ("running", "Running", ""),
        StageLifecycle.COMPLETED: ("completed", "Completed", "✓"),
        StageLifecycle.COMPLETED_WITH_WARNINGS: ("completed", "Completed with warnings", "✓"),
        StageLifecycle.FAILED: ("failed", "Failed", "!"),
    }
    return labels[lifecycle]


def _render_brief(brief: SearchBrief) -> str:
    requirements = f'<p class="run-copy">{escape(brief.requirements)}</p>' if brief.requirements else ""
    return f"""<section><p class="run-kicker">Search Brief</p><h2 class="run-title">{escape(brief.purpose)}</h2>{requirements}<div class="run-chips"><span class="run-chip">{escape(brief.domain)}</span><span class="run-chip">{escape(brief.data_type)}</span></div></section>"""


def _render_stages(run: RunRecord) -> str:
    rows = []
    for number, stage in enumerate(Stage, 1):
        css, label, marker = _stage_state(run.stage_history[stage])
        rows.append(f'<li class="run-stage {css}"><span class="run-marker">{marker or number}</span><strong>{escape(_STAGE_LABELS[stage])}</strong><span class="run-status">{label}</span></li>')
    return f'<ol class="run-stage-list">{"".join(rows)}</ol>'


def _counts_markup(counts: list[Count]) -> str:
    return " ".join(
        f'<span class="run-chip">{count.value} {escape(count.label)}</span>' for count in counts
    )


def _render_activity(run: RunRecord, current_activity: ActivityEvent | None) -> str:
    updates = [event for event in run.events if isinstance(event, ActivityEvent)]
    current = ""
    if current_activity:
        current = f'<div class="run-activity-panel"><p class="run-kicker">In progress</p><h2 class="run-title">{escape(_STAGE_LABELS[current_activity.stage])}</h2><p class="run-copy">{escape(current_activity.message)}</p></div>'
    history = "".join(
        f'<li class="run-activity"><span class="run-activity-marker">✓</span><div>'
        f'<strong>{escape(_STAGE_LABELS[event.stage])}</strong>'
        f'<p class="run-copy">{escape(event.message)}</p>'
        f"{_counts_markup(event.counts)}"
        "</div></li>"
        for event in updates
        if event is not current_activity
    )
    history_block = f'<ol class="run-activity-list">{history}</ol>' if history else '<p class="run-copy">Progress updates will appear here as each Stage completes.</p>'
    return f'<section aria-live="polite"><p class="run-kicker">Run Activity</p>{current}<div class="run-activity-panel"><p class="run-kicker">Completed updates</p>{history_block}</div></section>'


def _candidate_by_id(candidates: list[ResultCandidate]) -> dict[str, ResultCandidate]:
    return {candidate.id: candidate for candidate in candidates}


def _check_markup(check: RequirementCheck) -> str:
    labels = {"met": "Meets", "partial": "Partially meets", "not_met": "Does not meet", "unknown": "Not verified"}
    citation = ""
    if check.citation:
        citation = f' <a href="{escape(check.citation.source_url, quote=True)}" target="_blank" rel="noopener noreferrer">Evidence ↗</a>'
    return f'<li class="run-check"><strong>{escape(check.requirement)}</strong><span class="run-check-status {check.status}">{labels[check.status]}</span><p>{escape(check.note)}{citation}</p></li>'


def _result_markup(evaluation: CandidateEvaluation, candidate: ResultCandidate) -> str:
    issues = " ".join(escape(issue.summary) for issue in evaluation.known_issues) or "No material limitation was identified."
    checks = "".join(_check_markup(check) for check in evaluation.requirement_checks) or '<li class="run-check"><p>No Requirement Checks were produced.</p></li>'
    return f'''<details class="run-result"><summary><div class="run-result-top"><span class="run-result-meta"><span class="run-rank">Rank {evaluation.rank}</span><span class="run-source">{escape(candidate.source)}</span></span><span class="run-status">View assessment</span></div><h3>{escape(candidate.name)}</h3><p class="run-copy">{escape(evaluation.fit_summary)}</p></summary><div class="run-result-body"><p class="run-kicker">Requirement Checks</p><ol class="run-checks">{checks}</ol><div class="run-result-actions"><p class="run-copy"><strong>Result limitation:</strong> {issues}</p><a href="{escape(candidate.url, quote=True)}" target="_blank" rel="noopener noreferrer">Open dataset ↗</a></div></div></details>'''


def _render_results(run: RunRecord) -> str:
    assert run.results is not None
    candidates = _candidate_by_id(run.results.candidates)
    cards = [_result_markup(evaluation, candidates[evaluation.candidate_id]) for evaluation in sorted(run.results.evaluations, key=lambda item: item.rank) if evaluation.candidate_id in candidates]
    shown, remaining = cards[:3], cards[3:]
    reveal = (
        '<details class="run-show-all"><summary>'
        f'<span class="run-top-label">Show all {len(cards)} Results</span>'
        f'<span class="run-all-label">All {len(cards)} Results shown</span>'
        f'</summary>{"".join(remaining)}</details>'
        if remaining
        else ""
    )
    return f'<section><div class="run-results-head"><div><p class="run-kicker">Ranked Results</p><h2 class="run-title">{escape(run.results.overview)}</h2></div><span class="run-rank"><span class="run-top-label">Top {min(3, len(cards))} shown</span><span class="run-all-label">All {len(cards)} shown</span></span></div><div class="run-result-list">{"".join(shown)}{reveal}</div></section>'


def render_run_view(run: RunRecord, search_brief: SearchBrief, *, show_results: bool = True, current_activity: ActivityEvent | None = None) -> str:
    """Render the split Run View using only user-safe Run data."""
    rail = f'{_render_brief(search_brief)}{_render_stages(run)}'
    if show_results and run.results:
        rail = f'<p class="run-kicker">Completed Run</p><details class="run-details"><summary>Search Brief and Stage history</summary>{rail}</details>'
        main = f'<div class="run-summary run-terminal"><p class="run-kicker">Run summary</p><h2 class="run-title">Completed all four Stages.</h2></div>{_render_results(run)}'
    elif show_results:
        label = {
            RunOutcome.CANCELLED: "Cancelled",
            RunOutcome.FAILED: "Failed",
            RunOutcome.EMPTY_RESULTS: "Empty Results",
            RunOutcome.COMPLETED_WITH_WARNINGS: "Completed with warnings",
        }.get(run.outcome, "Completed")
        main = f'<div class="run-summary run-terminal"><p class="run-kicker">Run summary</p><h2 class="run-title">{label}</h2><p class="run-copy">No Results were produced for this Run.</p></div>'
    else:
        main = _render_activity(run, current_activity)
    return f'{_CSS}<main class="run-view"><article class="run-view-shell"><div class="run-view-grid"><aside class="run-rail">{rail}</aside><section class="run-main">{main}</section></div></article></main>'
