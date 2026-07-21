"""Gradio / HuggingFace Spaces entry point."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent


def _load_env() -> None:
    env_path = ROOT / ".env"
    if env_path.exists():
        print("Loading .env...", flush=True)
        load_dotenv(env_path)


def _load_gradio():
    print("Loading Gradio...", flush=True)
    import gradio

    return gradio


_load_env()
gr = _load_gradio()


SAMPLE_QUERY = {
    "purpose": "train a sentiment classifier for short product reviews",
    "domain": "natural language processing",
    "data_type": "labeled text classification dataset",
    "requirements": (
        "English text, sentiment labels, at least 10k examples, permissive license preferred"
    ),
    "additional_notes": "Prefer datasets with clear train/test splits and dataset cards.",
    "exclude_datasets": "imdb",
}


def _s(value: str | None) -> str:
    return (value or "").strip()


def _run(
    api_key: str | None,
    purpose: str | None,
    domain: str | None,
    data_type: str | None,
    requirements: str | None,
    additional_notes: str | None,
    exclude_datasets: str | None,
) -> Iterator[str]:
    key = _s(api_key)
    if not key:
        yield "**Error:** Gemini API key is required."
        return
    if not all([_s(purpose), _s(domain), _s(data_type)]):
        yield "**Error:** Purpose, domain, and data type are all required."
        return

    yield "*Running SetScout pipeline (search → evidence → evaluate). This can take a minute...*"
    try:
        yield "*Loading SetScout pipeline...*"
        from setscout.pipeline import run_pipeline

        result = run_pipeline(
            {
                "purpose": _s(purpose),
                "domain": _s(domain),
                "data_type": _s(data_type),
                "requirements": _s(requirements),
                "additional_notes": _s(additional_notes),
                "exclude_datasets": _s(exclude_datasets),
            },
            api_key=key,
        )
        yield result.get("report") or "No report produced."
    except Exception as e:
        yield f"**Error:** {type(e).__name__}: {e}"


with gr.Blocks(title="SetScout") as demo:
    gr.Markdown("# SetScout\nAgentic dataset discovery and evaluation for ML researchers.")

    with gr.Row():
        api_key = gr.Textbox(
            label="Gemini API Key",
            type="password",
            value="",
            placeholder="AIza...",
        )

    gr.Markdown("### Required")
    with gr.Row():
        purpose = gr.Textbox(
            label="Purpose",
            value=SAMPLE_QUERY["purpose"],
            placeholder="e.g. train a sentiment classifier",
        )
        domain = gr.Textbox(
            label="Domain",
            value=SAMPLE_QUERY["domain"],
            placeholder="e.g. natural language processing",
        )
        data_type = gr.Textbox(
            label="Data type",
            value=SAMPLE_QUERY["data_type"],
            placeholder="e.g. labeled text",
        )

    gr.Markdown("### Optional")
    with gr.Row():
        requirements = gr.Textbox(
            label="Requirements",
            value=SAMPLE_QUERY["requirements"],
            lines=3,
            placeholder="e.g. min 10k samples, English, permissive license",
        )
        additional_notes = gr.Textbox(
            label="Additional notes",
            value=SAMPLE_QUERY["additional_notes"],
            lines=3,
            placeholder="Any other context for the search",
        )
    exclude_datasets = gr.Textbox(
        label="Exclude datasets",
        value=SAMPLE_QUERY["exclude_datasets"],
        placeholder="Comma-separated dataset names to exclude",
    )

    run_btn = gr.Button("Run", variant="primary")
    output = gr.Markdown(value="")

    run_btn.click(
        fn=_run,
        inputs=[
            api_key,
            purpose,
            domain,
            data_type,
            requirements,
            additional_notes,
            exclude_datasets,
        ],
        outputs=output,
        api_name="run",
    )

demo.queue()

if __name__ == "__main__":
    # ssr_mode=False: avoids Node SSR flakiness on WSL / some Spaces hosts
    print("Launching SetScout UI...", flush=True)
    demo.launch(show_error=True, ssr_mode=False)
