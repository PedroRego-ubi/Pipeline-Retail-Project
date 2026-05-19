"""
Reads all upstream artifacts and produces quality_report.json.

Checks:
  - Schema validity of every output artifact
  - Metric grounding: every evidence_metric in insights.json exists in metrics.json
  - Stitcher reproducibility: re-runs stitcher and diffs the result
  - Threshold sensitivity: re-runs stitcher with ±20% on MAX_GAP_S
  - Data quality signals: orphan rate, mean stitch confidence, completion rate

Public API:
    run_evaluate(config)
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

import pandas as pd

from src.utils import read_json, write_json, timer

logger = logging.getLogger(__name__)


def run_evaluate(config: dict) -> None:
    pass


def _validate_schemas(config: dict) -> dict:
    pass


def _check_grounding(insights: dict, metrics: dict) -> dict:
    pass


def _check_reproducibility(config: dict) -> dict:
    pass


def _sensitivity_analysis(config: dict) -> dict:
    pass


def _data_quality_summary(config: dict) -> dict:
    pass


def _resolve_metric(metrics: dict, dotted_path: str) -> bool:
    """Return True if dotted_path resolves to a value in the metrics dict."""
    pass
