"""Gradio / HuggingFace Spaces entry point."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from dotenv import load_dotenv

from setscout.presentation import render_ledger
from setscout.replay import load_practice_run

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


def _render_practice_run() -> str:
    """Render the checked-in Ledger example without credentials or network access."""
    replay = load_practice_run()
    return render_ledger(replay.run, replay.search_brief)


def _open_practice_run():
    """Show the Ledger and hide the legacy Markdown output."""
    return gr.Markdown(value="", visible=False), gr.HTML(
        value=_render_practice_run(), visible=True
    )


def _run(
    api_key: str | None,
    purpose: str | None,
    domain: str | None,
    data_type: str | None,
    requirements: str | None,
    additional_notes: str | None,
    exclude_datasets: str | None,
) -> Iterator[tuple]:
    key = _s(api_key)
    if not key:
        yield gr.Markdown(value="**Error:** Gemini API key is required.", visible=True), gr.HTML(
            visible=False
        )
        return
    if not all([_s(purpose), _s(domain), _s(data_type)]):
        yield gr.Markdown(
            value="**Error:** Purpose, domain, and data type are all required.", visible=True
        ), gr.HTML(visible=False)
        return

    yield gr.Markdown(
        value=(
            "*Running SetScout pipeline (search → evidence → evaluate). This can take a minute...*"
        ),
        visible=True,
    ), gr.HTML(visible=False)
    try:
        yield gr.Markdown(value="*Loading SetScout pipeline...*", visible=True), gr.HTML(
            visible=False
        )
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
        yield (
            gr.Markdown(value=result.get("report") or "No report produced.", visible=True),
            gr.HTML(visible=False),
        )
    except Exception as e:
        yield gr.Markdown(value=f"**Error:** {type(e).__name__}: {e}", visible=True), gr.HTML(
            visible=False
        )


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

    with gr.Row():
        run_btn = gr.Button("Run", variant="primary")
        practice_btn = gr.Button("Open practice Run")
    markdown_output = gr.Markdown(visible=False)
    ledger_output = gr.HTML(value=_render_practice_run())

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
        outputs=[markdown_output, ledger_output],
        api_name="run",
    )
    practice_btn.click(
        fn=_open_practice_run,
        outputs=[markdown_output, ledger_output],
        api_name="practice-run",
    )

demo.queue()

if __name__ == "__main__":
    # ssr_mode=False: avoids Node SSR flakiness on WSL / some Spaces hosts
    print("Launching SetScout UI...", flush=True)
    demo.launch(show_error=True, ssr_mode=False)
