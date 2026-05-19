"""
Schema validation tests for every pipeline output artifact.
Runs after a full pipeline execution — skips gracefully if artifacts don't exist yet.
"""

import json
import pytest
from pathlib import Path


JOURNEYS_COLUMNS = {
    "journey_id", "start_time", "end_time", "duration_total_s",
    "n_events", "n_zones_visited", "zones_sequence", "start_zone",
    "end_zone", "gender", "age_range", "completed", "day_of_week",
    "hour_of_day", "stitch_confidence",
}

METRICS_TOP_KEYS = {
    "metadata", "summary", "traffic", "zones",
    "demographics", "journey_patterns", "data_quality",
}

INSIGHTS_TOP_KEYS = {
    "metadata", "key_findings", "recommendations", "anomalies", "caveats",
}


def _load_json(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        pytest.skip(f"{path} does not exist — run the pipeline first")
    with open(p) as fh:
        return json.load(fh)


def test_metrics_json_schema():
    metrics = _load_json("outputs/metrics.json")
    missing = METRICS_TOP_KEYS - set(metrics.keys())
    assert not missing, f"metrics.json missing keys: {missing}"


def test_insights_json_schema():
    insights = _load_json("outputs/insights.json")
    missing = INSIGHTS_TOP_KEYS - set(insights.keys())
    assert not missing, f"insights.json missing keys: {missing}"


def test_insights_key_findings_have_required_fields():
    insights = _load_json("outputs/insights.json")
    for i, finding in enumerate(insights.get("key_findings", [])):
        for field in ("title", "claim", "evidence_metrics", "confidence"):
            assert field in finding, f"key_findings[{i}] missing field: {field!r}"


def test_grounding_all_evidence_metrics_exist():
    """Every evidence_metric in insights must resolve in metrics.json."""
    metrics = _load_json("outputs/metrics.json")
    insights = _load_json("outputs/insights.json")

    def resolve(d: dict, path: str) -> bool:
        parts = path.split(".")
        cur = d
        for part in parts:
            if not isinstance(cur, dict) or part not in cur:
                return False
            cur = cur[part]
        return True

    failures = []
    for section in ("key_findings", "recommendations", "anomalies"):
        for item in insights.get(section, []):
            for key in item.get("evidence_metrics", []):
                if not resolve(metrics, key):
                    failures.append(key)

    assert not failures, f"Unresolvable evidence_metrics: {failures}"


def test_quality_report_schema():
    report = _load_json("outputs/quality_report.json")
    for key in ("schema_validation", "grounding", "reproducibility", "sensitivity", "data_quality"):
        assert key in report, f"quality_report.json missing key: {key!r}"


def test_journeys_csv_columns():
    import pandas as pd
    p = Path("data/processed/journeys.csv")
    if not p.exists():
        pytest.skip("journeys.csv does not exist — run the pipeline first")
    df = pd.read_csv(p, nrows=0)
    missing = JOURNEYS_COLUMNS - set(df.columns)
    assert not missing, f"journeys.csv missing columns: {missing}"
