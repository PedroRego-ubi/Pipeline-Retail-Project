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
    pass


def _load_prompt(config: dict) -> str:
    pass


def _validate_insights(obj: dict) -> bool:
    pass
