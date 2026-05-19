"""
Loads metrics.json, loads the production prompt from prompts/, calls
llm_client.generate(), validates the JSON response against a schema,
writes insights.json.

If validation fails, writes a fallback insights.json with empty findings
and a caveat. Never crashes the pipeline — a degraded report is better
than no report.

Public API:
    run_insights(metrics_path, output_path, config)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from src import llm_client
from src.utils import read_json, write_json, timer

logger = logging.getLogger(__name__)

INSIGHTS_SCHEMA = {
    "metadata": dict,
    "key_findings": list,
    "recommendations": list,
    "anomalies": list,
    "caveats": list,
}

FALLBACK_INSIGHTS = {
    "metadata": {},
    "key_findings": [],
    "recommendations": [],
    "anomalies": [],
    "caveats": ["LLM output was unavailable or failed schema validation."],
}


def run_insights(metrics_path: str, output_path: str, config: dict) -> None:
    with timer("load_metrics", logger):
        metrics = read_json(metrics_path)

    prompt = _load_prompt(config)
    prompt = prompt.replace("{{ metrics_json }}", json.dumps(metrics, indent=2, default=str))

    llm_cfg = config.get("llm", {})
    with timer("llm_generate", logger):
        raw = llm_client.generate(
            prompt,
            schema=INSIGHTS_SCHEMA,
            model=llm_cfg.get("model", "llama3.1:8b"),
            temperature=llm_cfg.get("temperature", 0.0),
            base_url=llm_cfg.get("base_url", "http://localhost:11434"),
            timeout_s=llm_cfg.get("timeout_s", 120),
            max_retries=llm_cfg.get("max_retries", 2),
        )

    try:
        insights = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        logger.warning("Failed to parse LLM response as JSON: %s", exc)
        insights = None

    if insights is None or not _validate_insights(insights):
        logger.warning("Insights validation failed — writing fallback")
        insights = FALLBACK_INSIGHTS.copy()
        insights["metadata"] = {
            "generated_at": datetime.utcnow().isoformat(),
            "prompt_version": llm_cfg.get("prompt_version", "unknown"),
        }

    write_json(insights, output_path)
    logger.info("Insights written to %s", output_path)


def _load_prompt(config: dict) -> str:
    prompts_dir = Path(config.get("paths", {}).get("prompts_dir", "prompts/"))
    version = config.get("llm", {}).get("prompt_version", "v1_naive")
    prompt_path = prompts_dir / f"insights_{version}.txt"
    return prompt_path.read_text(encoding="utf-8")


def _validate_insights(obj: dict) -> bool:
    from src.utils import validate_schema
    errors = validate_schema(obj, INSIGHTS_SCHEMA)
    if errors:
        logger.warning("Schema errors: %s", errors)
        return False
    return True
