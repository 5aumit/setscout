"""The deterministic custom Ledger presentation for a public Run contract."""
from __future__ import annotations

from html import escape

from setscout.runs import RunOutcome, RunRecord, SearchBrief, Stage, StageLifecycle

_STAGE_LABELS = {
    Stage.PREPARE: "Prepare the Search Brief",
    Stage.SEARCH: "Search dataset sources",
    Stage.EVIDENCE: "Gather documentation evidence",
    Stage.EVALUATE: "Evaluate and rank candidates",
}


def _stage_label(lifecycle: StageLifecycle) -> str:
    return lifecycle.value.replace("_", " ").capitalize()


def _run_summary(outcome: RunOutcome) -> str:
    if outcome is RunOutcome.COMPLETED:
        return "Completed all four stages."
    if outcome is RunOutcome.COMPLETED_WITH_WARNINGS:
        return "Completed with warnings."
    if outcome is RunOutcome.EMPTY_RESULTS:
        return "Completed without ranked Results."
    if outcome is RunOutcome.CANCELLED:
        return "Cancelled before completion."
    return "Failed before Results could be produced."


def render_ledger(run: RunRecord, search_brief: SearchBrief) -> str:
    """Render a Run contract without knowing whether it came from live work or replay."""
    stages = "".join(
        f"<li><span class='ledger-number'>{index:02d}</span>"
        f"<span>{escape(_STAGE_LABELS[stage])}</span>"
        f"<strong>{escape(_stage_label(run.stage_history[stage]))}</strong></li>"
        for index, stage in enumerate(Stage, start=1)
    )
    requirements = (
        f"<p>{escape(search_brief.requirements)}</p>" if search_brief.requirements else ""
    )
    results = ""
    if run.results:
        cards = "".join(
            "<article class='result-card'><p class='rank'>Rank {rank}</p>"
            "<h3>{candidate}</h3><p>{summary}</p></article>".format(
                rank=evaluation.rank,
                candidate=escape(evaluation.candidate_id.replace("_", " ").title()),
                summary=escape(evaluation.fit_summary),
            )
            for evaluation in sorted(run.results.evaluations, key=lambda item: item.rank)
        )
        results = (
            "<section class='results'><p class='eyebrow'>Ranked Results</p>"
            f"<h2>{escape(run.results.overview)}</h2>"
            f"<div class='result-grid'>{cards}</div></section>"
        )
    return f"""
<style>
.ledger {{
  color: #dce8e9; background: #14272c; padding: 28px; font-family: Georgia, serif;
}}
.ledger-shell {{
  max-width: 1060px; margin: auto; display: grid;
  grid-template-columns: 280px 1fr; gap: 28px;
}}
.eyebrow, .rank {{
  color: #9cd2c9; font: 700 12px/1.2 ui-monospace, monospace;
  letter-spacing: .09em; text-transform: uppercase;
}}
.brief, .results {{
  background: #eff0e8; color: #17292d; padding: 24px;
}}
.brief h2, .results h2 {{ margin-top: 0; }}
.stage-list {{ list-style: none; padding: 0; margin: 0; }}
.stage-list li {{
  border-left: 2px solid #5a8180; display: grid; gap: 4px; padding: 0 0 20px 16px;
}}
.stage-list strong {{
  color: #9cd2c9; font: 700 12px/1.2 ui-monospace, monospace; text-transform: uppercase;
}}
.ledger-number {{ color: #f4bd62; font: 700 12px/1 ui-monospace, monospace; }}
.summary {{ border-top: 1px solid #5a8180; margin-top: 20px; padding-top: 16px; }}
.result-grid {{
  display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px;
}}
.result-card {{ border: 1px solid #9aaca7; padding: 16px; }}
@media (max-width: 700px) {{ .ledger-shell {{ grid-template-columns: 1fr; }} }}
@media (prefers-reduced-motion: reduce) {{
  * {{ transition: none !important; animation: none !important; }}
}}
</style>
<main class='ledger'>
  <div class='ledger-shell'>
    <aside>
      <p class='eyebrow'>{escape(_stage_label(run.outcome))} Run</p><h1>Ledger</h1>
      <ol class='stage-list'>{stages}</ol>
    </aside>
    <div>
      <section class='brief'>
        <p class='eyebrow'>Search Brief</p><h2>{escape(search_brief.purpose)}</h2>
        <p>{escape(search_brief.domain)} · {escape(search_brief.data_type)}</p>{requirements}
      </section>
      <section class='summary'>
        <p class='eyebrow'>Run Summary</p><p>{escape(_run_summary(run.outcome))}</p>
      </section>
      {results}
    </div>
  </div>
</main>
"""
