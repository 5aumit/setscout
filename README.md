# SetScout

Agentic dataset discovery and evaluation for ML researchers. Describe what you need in natural language; a LangGraph pipeline searches Hugging Face and Kaggle, scores candidates, and produces a structured report.

## Setup

```bash
conda env create -f environment.yml
conda activate setscout
pip install -e ".[dev]"
```

Create a repo-root `.env` with:

- `GEMINI_API_KEY`
- `KAGGLE_USERNAME` / `KAGGLE_KEY` (optional, for Kaggle search)
- `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL=https://us.cloud.langfuse.com` (optional, enables tracing)

## Run

Prototype notebook:

```bash
jupyter notebook notebooks/setscout_prototype.ipynb
```

Or from Python:

```python
from setscout import run_pipeline

result = run_pipeline({
    "purpose": "...",
    "domain": "...",
    "data_type": "...",
})
print(result["report"])
```

End-to-end smoke run with timestamped logs:

```bash
python -m scripts.run_pipeline_once
```
