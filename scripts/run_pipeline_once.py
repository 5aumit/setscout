from __future__ import annotations

import json
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from setscout import run_pipeline

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "logs"


REQUEST = {
    "purpose": "benchmark sentiment classification models for academic research",
    "domain": "natural language processing",
    "data_type": "text datasets",
    "requirements": (
        "English language, public access, labeled sentiment classes, at least 1000 examples"
    ),
    "additional_notes": "Prefer common benchmark datasets with clear documentation.",
    "exclude_datasets": "",
}


def to_jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    return value


def configure_logging() -> Path:
    LOG_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = LOG_DIR / f"pipeline-{timestamp}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    return log_path


def main() -> int:
    log_path = configure_logging()
    load_dotenv(dotenv_path=ROOT / ".env")

    logging.info("Writing pipeline output to %s", log_path)
    logging.info("Starting SetScout pipeline")
    logging.info("Request:\n%s", json.dumps(REQUEST, indent=2))

    try:
        result = run_pipeline(REQUEST)
    except Exception:
        logging.error("Pipeline failed")
        logging.error(traceback.format_exc())
        return 1

    output = to_jsonable(result)
    logging.info("Pipeline completed")
    logging.info("State keys: %s", sorted(output.keys()))
    logging.info("Pipeline logs:\n%s", json.dumps(output.get("logs", []), indent=2))
    logging.info("Search spec:\n%s", json.dumps(output.get("search_spec"), indent=2))
    logging.info("Candidates:\n%s", json.dumps(output.get("candidates", []), indent=2))
    logging.info("Evaluations:\n%s", json.dumps(output.get("evaluations", []), indent=2))
    logging.info("Report:\n%s", output.get("report", ""))
    logging.info("Finished. Log file: %s", log_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
