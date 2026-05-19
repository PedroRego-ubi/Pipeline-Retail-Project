"""
Loads metrics.json + insights.json, renders templates/weekly_report.md.j2
with Jinja2, writes weekly_report.md.

Pure templating — no LLM call here. The narrative was already produced in
insights.py. Report generation is deterministic and reproducible.

Public API:
    run_report(metrics_path, insights_path, output_path, config)
"""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from src.utils import read_json, timer


def run_report(
    metrics_path: str,
    insights_path: str,
    output_path: str,
    config: dict,
) -> None:
    pass


def _resolve(metrics: dict, dotted_path: str):
    """Walk a dotted key path into the metrics dict and return the value."""
    pass
