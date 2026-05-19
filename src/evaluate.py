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

import copy
import hashlib
import logging
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.utils import read_json, write_json, timer, validate_schema
from src.stitcher import run_stitcher

logger = logging.getLogger(__name__)

JOURNEYS_REQUIRED_COLS = {
    "journey_id", "start_time", "end_time", "duration_total_s",
    "n_events", "n_zones_visited", "zones_sequence", "start_zone",
    "end_zone", "gender", "age_range", "completed", "day_of_week",
    "hour_of_day", "stitch_confidence",
}

METRICS_SCHEMA = {
    "metadata": dict,
    "summary": dict,
    "traffic": dict,
    "zones": dict,
    "demographics": dict,
    "journey_patterns": dict,
    "data_quality": dict,
}

INSIGHTS_SCHEMA = {
    "metadata": dict,
    "key_findings": list,
    "recommendations": list,
    "anomalies": list,
    "caveats": list,
}


def run_evaluate(config: dict) -> None:
    paths = config["paths"]

    with timer("validate_schemas", logger):
        schema_results = _validate_schemas(config)

    with timer("check_grounding", logger):
        try:
            insights = read_json(paths["insights"])
            metrics = read_json(paths["metrics"])
            grounding_results = _check_grounding(insights, metrics)
        except Exception as exc:
            logger.warning("Grounding check skipped: %s", exc)
            grounding_results = {"error": str(exc)}

    with timer("check_reproducibility", logger):
        try:
            reproducibility_results = _check_reproducibility(config)
        except Exception as exc:
            logger.warning("Reproducibility check skipped: %s", exc)
            reproducibility_results = {"error": str(exc)}

    with timer("sensitivity_analysis", logger):
        try:
            sensitivity_results = _sensitivity_analysis(config)
        except Exception as exc:
            logger.warning("Sensitivity analysis skipped: %s", exc)
            sensitivity_results = {"error": str(exc)}

    with timer("data_quality_summary", logger):
        try:
            dq_summary = _data_quality_summary(config)
        except Exception as exc:
            logger.warning("Data quality summary skipped: %s", exc)
            dq_summary = {"error": str(exc)}

    report = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "schema_validation": schema_results,
        "metric_grounding": grounding_results,
        "reproducibility": reproducibility_results,
        "sensitivity_analysis": sensitivity_results,
        "data_quality": dq_summary,
    }

    write_json(report, paths["quality_report"])
    logger.info("Quality report written to %s", paths["quality_report"])


def _validate_schemas(config: dict) -> dict:
    paths = config["paths"]
    results = {}

    journeys_path = paths["journeys"]
    if not Path(journeys_path).exists():
        results["journeys"] = {"valid": False, "errors": ["File not found"]}
    else:
        df = pd.read_csv(journeys_path, nrows=0)
        missing = sorted(JOURNEYS_REQUIRED_COLS - set(df.columns))
        errors = [f"Missing columns: {missing}"] if missing else []
        results["journeys"] = {"valid": not errors, "errors": errors}

    metrics_path = paths["metrics"]
    if not Path(metrics_path).exists():
        results["metrics"] = {"valid": False, "errors": ["File not found"]}
    else:
        errors = validate_schema(read_json(metrics_path), METRICS_SCHEMA)
        results["metrics"] = {"valid": not errors, "errors": errors}

    insights_path = paths["insights"]
    if not Path(insights_path).exists():
        results["insights"] = {"valid": False, "errors": ["File not found"]}
    else:
        errors = validate_schema(read_json(insights_path), INSIGHTS_SCHEMA)
        results["insights"] = {"valid": not errors, "errors": errors}

    results["all_valid"] = all(v["valid"] for v in results.values() if isinstance(v, dict))
    return results


def _check_grounding(insights: dict, metrics: dict) -> dict:
    unresolved = []
    resolved = []

    for section in ("key_findings", "recommendations", "anomalies"):
        for item in insights.get(section, []):
            if isinstance(item, dict) and "evidence_metric" in item:
                path = item["evidence_metric"]
                if _resolve_metric(metrics, path):
                    resolved.append(path)
                else:
                    unresolved.append({"section": section, "path": path})

    return {
        "total_evidence_metrics": len(resolved) + len(unresolved),
        "resolved": len(resolved),
        "unresolved": unresolved,
        "grounded": len(unresolved) == 0,
    }


def _check_reproducibility(config: dict) -> dict:
    original_path = config["paths"]["journeys"]
    events_path = config["paths"]["events"]

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        run_stitcher(events_path, tmp_path, config)

        original_hash = _file_hash(original_path)
        reproduced_hash = _file_hash(tmp_path)

        orig_rows = len(pd.read_csv(original_path))
        repro_rows = len(pd.read_csv(tmp_path))
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return {
        "match": original_hash == reproduced_hash,
        "original_hash": original_hash,
        "reproduced_hash": reproduced_hash,
        "original_rows": orig_rows,
        "reproduced_rows": repro_rows,
        "row_delta": repro_rows - orig_rows,
    }


def _sensitivity_analysis(config: dict) -> dict:
    base_gap = config["stitcher"]["max_gap_s"]
    events_path = config["paths"]["events"]
    original_path = config["paths"]["journeys"]

    orig_df = pd.read_csv(original_path)
    baseline = {
        "n_journeys": len(orig_df),
        "completion_rate": round(float(orig_df["completed"].mean()), 4),
        "avg_stitch_confidence": round(float(orig_df["stitch_confidence"].mean()), 4),
    }

    variants = {}
    for label, multiplier in [("minus_20pct", 0.8), ("plus_20pct", 1.2)]:
        cfg_variant = copy.deepcopy(config)
        cfg_variant["stitcher"]["max_gap_s"] = int(base_gap * multiplier)

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            run_stitcher(events_path, tmp_path, cfg_variant)
            v_df = pd.read_csv(tmp_path)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

        v_completion = round(float(v_df["completed"].mean()), 4)
        v_confidence = round(float(v_df["stitch_confidence"].mean()), 4)

        variants[label] = {
            "max_gap_s": cfg_variant["stitcher"]["max_gap_s"],
            "n_journeys": len(v_df),
            "n_journeys_delta": len(v_df) - baseline["n_journeys"],
            "completion_rate": v_completion,
            "completion_rate_delta": round(v_completion - baseline["completion_rate"], 4),
            "avg_stitch_confidence": v_confidence,
            "avg_confidence_delta": round(v_confidence - baseline["avg_stitch_confidence"], 4),
        }

    return {
        "base_max_gap_s": base_gap,
        "baseline": baseline,
        "variants": variants,
    }


def _data_quality_summary(config: dict) -> dict:
    df = pd.read_csv(config["paths"]["journeys"])
    n = len(df)
    orphan_threshold = 1.0 - config["stitcher"]["confidence"]["orphan_penalty"]

    return {
        "n_journeys": n,
        "mean_stitch_confidence": round(float(df["stitch_confidence"].mean()), 4),
        "completion_rate": round(float(df["completed"].mean()), 4),
        "orphan_proxy_rate": round(float((df["stitch_confidence"] < orphan_threshold).mean()), 4),
        "low_confidence_rate": round(float((df["stitch_confidence"] < 0.5).mean()), 4),
        "force_closed_rate": round(float((~df["completed"]).mean()), 4),
    }


def _resolve_metric(metrics: dict, dotted_path: str) -> bool:
    """Return True if dotted_path resolves to a value in the metrics dict."""
    node = metrics
    for part in dotted_path.split("."):
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return False
    return True


def _file_hash(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()
