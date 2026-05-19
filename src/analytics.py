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

from collections import Counter

from src.utils import setup_logger, write_json, timer


def run_analytics(journeys_path: str, output_path: str, config: dict) -> None:
    logger = setup_logger("analytics", config["paths"]["logs_dir"])

    with timer("Load journeys", logger):
        df = pd.read_csv(journeys_path, parse_dates=["start_time", "end_time"])

    logger.info(f"Loaded {len(df):,} journeys")

    with timer("Compute metrics", logger):
        jpd = df.groupby(df["start_time"].dt.date).size().to_dict()
        
        metrics = {
            "metadata": {
                "generated_at": pd.Timestamp.now().isoformat(),
                "journeys_path": str(journeys_path),
                "n_journeys": len(df),
            },
            "summary": _build_summary(df),
            "traffic": _build_traffic(df, config),
            "zones": _build_zones(df, config),
            "demographics": _build_demographics(df),
            "journey_patterns": _build_journey_patterns(df, config),
            "data_quality": _build_data_quality(df),
            # FIX: Export the new metric as a string-keyed dictionary
            "journeys_per_day": {str(k): int(v) for k, v in jpd.items()},
        }

    with timer("Write metrics", logger):
        write_json(metrics, output_path)

    logger.info(f"Wrote metrics to {output_path}")


def _build_summary(df: pd.DataFrame) -> dict:
    n = len(df)
    completed = int(df["completed"].sum())
    return {
        "total_journeys": n,
        "completed_journeys": completed,
        "completion_rate": round(completed / n, 4) if n > 0 else 0.0,
        "avg_duration_s": round(float(df["duration_total_s"].mean()), 1),
        "median_duration_s": round(float(df["duration_total_s"].median()), 1),
        "std_duration_s": round(float(df["duration_total_s"].std()), 1),
        "avg_zones_per_journey": round(float(df["n_zones_visited"].mean()), 2),
        "avg_events_per_journey": round(float(df["n_events"].mean()), 2),
        "avg_stitch_confidence": round(float(df["stitch_confidence"].mean()), 4),
        "date_range": {
            "start": str(df["start_time"].min()),
            "end": str(df["end_time"].max()),
        },
    }


def _build_traffic(df: pd.DataFrame, config: dict) -> dict:
    peak_multiplier: float = config["analytics"]["peak_hour_multiplier"]

    hourly = df.groupby("hour_of_day").size()
    mean_hourly = float(hourly.mean())
    peak_hours = sorted(int(h) for h in hourly[hourly > peak_multiplier * mean_hourly].index)

    daily = df.groupby("day_of_week").size()
    hourly_avg_dur = df.groupby("hour_of_day")["duration_total_s"].mean()

    return {
        "by_hour": {str(k): int(v) for k, v in hourly.items()},
        "by_day_of_week": {str(k): int(v) for k, v in daily.items()},
        "peak_hours": peak_hours,
        "mean_hourly_journeys": round(mean_hourly, 1),
        "hourly_avg_duration_s": {str(k): round(float(v), 1) for k, v in hourly_avg_dur.items()},
    }


def _build_zones(df: pd.DataFrame, config: dict) -> dict:
    visit_counter: Counter = Counter()
    for seq in df["zones_sequence"].dropna():
        for z in str(seq).split(";"):
            if z:
                visit_counter[z] += 1

    entry_counts = df["start_zone"].value_counts().to_dict()
    exit_counts = df["end_zone"].value_counts().to_dict()

    return {
        "entry_counts": {k: int(v) for k, v in entry_counts.items()},
        "exit_counts": {k: int(v) for k, v in exit_counts.items()},
        "visit_counts": {k: v for k, v in visit_counter.most_common()},
        "total_zone_visits": int(sum(visit_counter.values())),
        "most_entered": max(entry_counts, key=entry_counts.get) if entry_counts else None,
        "most_exited": max(exit_counts, key=exit_counts.get) if exit_counts else None,
        "most_visited": visit_counter.most_common(1)[0][0] if visit_counter else None,
    }


def _build_demographics(df: pd.DataFrame) -> dict:
    n = len(df)

    def _segment_stats(col: str) -> dict:
        return {
            str(val): {
                "count": int(cnt),
                "pct": round(cnt / n, 4),
                "avg_duration_s": round(
                    float(df.loc[df[col] == val, "duration_total_s"].mean()), 1
                ),
            }
            for val, cnt in df[col].value_counts().items()
        }

    return {
        "by_gender": _segment_stats("gender"),
        "by_age_range": _segment_stats("age_range"),
    }


def _build_journey_patterns(df: pd.DataFrame, config: dict) -> dict:
    top_n: int = config["analytics"]["top_paths_count"]
    min_len: int = config["analytics"]["top_paths_min_length"]
    n = len(df)

    long_journeys = df[df["n_zones_visited"] >= min_len]
    path_counts = long_journeys["zones_sequence"].value_counts()

    top_paths = [
        {"path": str(path), "count": int(count), "pct": round(count / n, 4)}
        for path, count in path_counts.head(top_n).items()
    ]

    single_zone = int((df["n_zones_visited"] == 1).sum())

    return {
        "top_paths": top_paths,
        "single_zone_journeys": single_zone,
        "single_zone_rate": round(single_zone / n, 4) if n > 0 else 0.0,
        "avg_zones_per_journey": round(float(df["n_zones_visited"].mean()), 2),
        "max_zones_in_journey": int(df["n_zones_visited"].max()),
    }


def _build_data_quality(df: pd.DataFrame) -> dict:
    n = len(df)
    low_conf = int((df["stitch_confidence"] < 0.5).sum())
    force_closed = int((~df["completed"]).sum())
    missing = {
        col: int(df[col].isna().sum())
        for col in df.columns
        if df[col].isna().any()
    }

    return {
        "total_rows": n,
        "force_closed_journeys": force_closed,
        "force_closed_rate": round(force_closed / n, 4) if n > 0 else 0.0,
        "low_confidence_journeys": low_conf,
        "low_confidence_rate": round(low_conf / n, 4) if n > 0 else 0.0,
        "avg_stitch_confidence": round(float(df["stitch_confidence"].mean()), 4),
        "missing_values": missing,
    }
