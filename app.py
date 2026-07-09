"""Gradio / HuggingFace Spaces entry point."""

from __future__ import annotations

import gradio as gr

from setscout.pipeline import run_pipeline


def _run(
    api_key: str,
    purpose: str,
    domain: str,
    data_type: str,
    requirements: str,
    additional_notes: str,
    exclude_datasets: str,
) -> str:
    if not (api_key or "").strip():
        return "**Error:** Gemini API key is required."
    if not all([purpose.strip(), domain.strip(), data_type.strip()]):
        return "**Error:** Purpose, domain, and data type are all required."
    try:
        result = run_pipeline(
            {
                "purpose": purpose,
                "domain": domain,
                "data_type": data_type,
                "requirements": requirements,
                "additional_notes": additional_notes,
                "exclude_datasets": exclude_datasets,
            },
            api_key=api_key.strip(),
        )
        return result.get("report") or "No report produced."
    except Exception as e:
        return f"**Error:** {e}"


with gr.Blocks(title="SetScout") as demo:
    gr.Markdown("# SetScout\nAgentic dataset discovery and evaluation for ML researchers.")

    with gr.Row():
        api_key = gr.Textbox(
            label="Gemini API Key",
            type="password",
            placeholder="AIza...",
        )

    gr.Markdown("### Required")
    with gr.Row():
        purpose = gr.Textbox(label="Purpose", placeholder="e.g. train a sentiment classifier")
        domain = gr.Textbox(label="Domain", placeholder="e.g. natural language processing")
        data_type = gr.Textbox(label="Data type", placeholder="e.g. labeled text")

    gr.Markdown("### Optional")
    with gr.Row():
        requirements = gr.Textbox(
            label="Requirements",
            lines=3,
            placeholder="e.g. min 10k samples, English, permissive license",
        )
        additional_notes = gr.Textbox(
            label="Additional notes",
            lines=3,
            placeholder="Any other context for the search",
        )
    exclude_datasets = gr.Textbox(
        label="Exclude datasets",
        placeholder="Comma-separated dataset names to exclude",
    )

    run_btn = gr.Button("Run", variant="primary")
    output = gr.Markdown(label="Report")

    run_btn.click(
        fn=_run,
        inputs=[api_key, purpose, domain, data_type, requirements, additional_notes, exclude_datasets],
        outputs=output,
    )

demo.queue()

if __name__ == "__main__":
    demo.launch()
