from __future__ import annotations

from setscout.graph.state import SetScoutState, log


def node_reporter(state: SetScoutState) -> dict:
    lines = ["# SetScout Report\n", f"**Purpose:** {state['query'].purpose}\n"]
    for i, sd in enumerate(state.get("scored_datasets") or [], 1):
        c, s = sd.candidate, sd.scores
        lines.append(f"\n## {i}. {c.name} ({c.source})\n")
        lines.append(f"- URL: {c.url}\n")
        lines.append(f"- **Final score:** {s.final_score}\n")
        lines.append(
            f"- Layer 1: size={s.layer1.size_fit}, metadata={s.layer1.metadata_fit}, access={s.layer1.access_fit}\n"
        )
        lines.append(
            f"- Layer 2: labels={s.layer2.label_quality}, issues={s.layer2.issue_severity}, fit={s.layer2.purpose_fit}\n"
        )
        if s.layer2.reasoning:
            lines.append(f"- Reasoning: {s.layer2.reasoning}\n")
        if c.known_issues:
            lines.append(f"- Known issues: {', '.join(c.known_issues)}\n")
    report = "".join(lines)
    return {"report": report, **log("reporter: done")}
