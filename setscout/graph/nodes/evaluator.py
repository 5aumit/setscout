from __future__ import annotations

from setscout.graph.state import SetScoutState, log
from setscout.models import PipelineResult, has_complete_ranking


def _build_prompt(state: SetScoutState) -> str:
    q = state["query"]
    constraints = state["search_spec"].hard_constraints
    candidates = state["candidates"]

    lines = [
        "You are evaluating dataset candidates for an ML researcher.",
        "",
        "## User requirements",
        f"Purpose: {q.purpose}",
        f"Domain: {q.domain}",
        f"Data type: {q.data_type}",
    ]
    if q.requirements:
        lines.append(f"Requirements: {q.requirements}")
    if q.additional_notes:
        lines.append(f"Notes: {q.additional_notes}")
    if constraints.min_samples:
        lines.append(f"Minimum samples: {constraints.min_samples}")
    if constraints.access:
        lines.append(f"Access requirement: {constraints.access}")

    lines += ["", "## Dataset candidates"]
    for c in candidates:
        lines.append(f"\n### [{c.id}] {c.name} ({c.source})")
        lines.append(f"URL: {c.url}")
        if c.evidence_docs:
            lines.append("Documentation excerpt:")
            lines.append(c.evidence_docs[0].text)
        else:
            lines.append("Documentation: not available")

    lines += [
        "",
        "## Instructions",
        "For each candidate:",
        "1. Check every stated requirement (met / partial / not_met / unknown). "
        "Base checks only on "
        "the documentation above — do not guess. Every status other than unknown must include a "
        "citation with source_kind, source_url, and a supporting excerpt.",
        "2. List any documentation-backed issues found (label noise, access restrictions, known "
        "limitations). Leave empty if none are stated.",
        "3. Write a one-sentence fit_summary.",
        "4. Assign a rank (1 = best fit).",
        "",
        "Then write a report_markdown: a concise human-readable report listing all datasets in "
        "rank order with their requirement checks, issues, and fit summary.",
        "Use markdown with headers, bullet points, and URLs.",
    ]
    return "\n".join(lines)


def node_evaluator(state: SetScoutState, *, llm) -> dict:
    candidates = state["candidates"]
    if not candidates:
        return {
            "evaluations": [],
            "report": "# SetScout Results\n\nNo candidates found.",
            **log("evaluator: no candidates"),
        }

    structured = llm.with_structured_output(PipelineResult)
    prompt = _build_prompt(state)

    try:
        result: PipelineResult = structured.invoke(prompt)
        evaluations = sorted(result.evaluations, key=lambda e: e.rank)
        if not has_complete_ranking(candidates, evaluations):
            raise ValueError("evaluator returned an incomplete ranking")
        return {
            "evaluations": evaluations,
            "report": result.report_markdown,
            **log(f"evaluator: evaluated {len(evaluations)} candidates"),
        }
    except Exception as exc:
        return {
            "evaluation_failed": True,
            **log(f"evaluator: evaluation failed ({type(exc).__name__})"),
        }
