from __future__ import annotations

from setscout.graph.state import SetScoutState, log
from setscout.models import CandidateEvaluation, PipelineResult


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
        "1. Check every stated requirement (met / partial / not_met / unknown). Base checks only on the documentation above — do not guess.",
        "2. List any documentation-backed issues found (label noise, access restrictions, known limitations). Leave empty if none are stated.",
        "3. Write a one-sentence fit_summary.",
        "4. Assign a rank (1 = best fit).",
        "",
        "Then write a report_markdown: a concise human-readable report listing all datasets in rank order with their requirement checks, issues, and fit summary.",
        "Use markdown with headers, bullet points, and URLs.",
    ]
    return "\n".join(lines)


def _fallback_report(candidates, error: str) -> tuple[list[CandidateEvaluation], str]:
    evals = []
    for i, c in enumerate(candidates, 1):
        evals.append(CandidateEvaluation(
            candidate_id=c.id,
            rank=i,
            fit_summary="Evaluation unavailable.",
        ))
    lines = ["# SetScout Results\n", f"*Evaluation failed: {error}*\n"]
    for i, c in enumerate(candidates, 1):
        lines.append(f"\n## {i}. {c.name} ({c.source})\n- URL: {c.url}\n")
    return evals, "".join(lines)


def node_evaluator(state: SetScoutState, *, llm) -> dict:
    candidates = state["candidates"]
    if not candidates:
        return {"evaluations": [], "report": "# SetScout Results\n\nNo candidates found.", **log("evaluator: no candidates")}

    structured = llm.with_structured_output(PipelineResult)
    prompt = _build_prompt(state)

    try:
        result: PipelineResult = structured.invoke(prompt)
        evaluations = sorted(result.evaluations, key=lambda e: e.rank)
        return {
            "evaluations": evaluations,
            "report": result.report_markdown,
            **log(f"evaluator: evaluated {len(evaluations)} candidates"),
        }
    except Exception as exc:
        evals, report = _fallback_report(candidates, str(exc))
        return {
            "evaluations": evals,
            "report": report,
            **log(f"evaluator: LLM failed ({type(exc).__name__}), used fallback report"),
        }
