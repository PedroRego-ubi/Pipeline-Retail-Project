"""
Reads journeys.csv, computes all aggregated metrics, writes metrics.json.

Pure pandas. No LLM, no I/O beyond read-in / write-out.
This module is what guarantees the LLM never sees raw data —
if it's not in metrics.json, the LLM cannot reference it.

Public API:
    run_analytics(journeys_path, output_path, config)
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import numpy as np

from src.utils import write_json, timer


def run_analytics(journeys_path: str, output_path: str, config: dict) -> None:
    pass


def _build_summary(df: pd.DataFrame) -> dict:
    pass


def _build_traffic(df: pd.DataFrame, config: dict) -> dict:
    pass


def _build_zones(df: pd.DataFrame, config: dict) -> dict:
    pass


def _build_demographics(df: pd.DataFrame) -> dict:
    pass


def _build_journey_patterns(df: pd.DataFrame, config: dict) -> dict:
    pass


def _build_data_quality(df: pd.DataFrame) -> dict:
    pass
