"""
Unit tests for stitcher.py using a hand-built synthetic event CSV
with known ground-truth journeys.
"""

import io
import pytest
import pandas as pd


SYNTHETIC_EVENTS_CSV = """event_id,timestamp,zone_id,event_type,duration_s,gender,age_range
E001,2026-05-19 09:00:00,Z1,entry,0,M,26-35
E002,2026-05-19 09:05:00,Z1,linger,300,M,26-35
E003,2026-05-19 09:15:00,Z2,linger,600,M,26-35
E004,2026-05-19 09:20:00,Z2,exit,0,M,26-35
E005,2026-05-19 09:01:00,Z3,entry,0,F,18-25
E006,2026-05-19 09:10:00,Z3,linger,540,F,18-25
E007,2026-05-19 09:25:00,Z1,exit,0,F,18-25
E008,2026-05-19 10:00:00,Z1,entry,0,M,26-35
E009,2026-05-19 12:30:00,Z2,linger,300,M,26-35
"""

BASE_CONFIG = {
    "stitcher": {
        "max_gap_s": 1800,
        "max_journey_s": 7200,
        "confidence": {
            "orphan_penalty": 0.10,
            "no_exit_penalty": 0.20,
            "near_threshold_gap_penalty": 0.10,
            "near_threshold_gap_ratio": 0.70,
        },
    }
}


@pytest.fixture
def synthetic_csv(tmp_path):
    p = tmp_path / "events.csv"
    p.write_text(SYNTHETIC_EVENTS_CSV.strip())
    return str(p)


@pytest.fixture
def journeys_output(tmp_path):
    return str(tmp_path / "journeys.csv")


def test_stitcher_produces_two_complete_journeys(synthetic_csv, journeys_output):
    from src.stitcher import run_stitcher
    run_stitcher(synthetic_csv, journeys_output, BASE_CONFIG)
    df = pd.read_csv(journeys_output)
    complete = df[df["completed"] == True]
    assert len(complete) == 2, f"Expected 2 complete journeys, got {len(complete)}"


def test_stitcher_gap_exceeds_max_gap_creates_new_journey(synthetic_csv, journeys_output):
    """E008 and E009 are 9000s apart — should not be stitched into one journey."""
    from src.stitcher import run_stitcher
    run_stitcher(synthetic_csv, journeys_output, BASE_CONFIG)
    df = pd.read_csv(journeys_output)
    male_26_35 = df[df["gender"] == "M"]
    assert len(male_26_35) >= 2, "E008 and E009 should produce a second journey for M/26-35"


def test_stitcher_is_deterministic(synthetic_csv, journeys_output, tmp_path):
    from src.stitcher import run_stitcher
    out2 = str(tmp_path / "journeys2.csv")
    run_stitcher(synthetic_csv, journeys_output, BASE_CONFIG)
    run_stitcher(synthetic_csv, out2, BASE_CONFIG)
    df1 = pd.read_csv(journeys_output)
    df2 = pd.read_csv(out2)
    pd.testing.assert_frame_equal(df1, df2)


def test_stitch_confidence_complete_journey(synthetic_csv, journeys_output):
    from src.stitcher import run_stitcher
    run_stitcher(synthetic_csv, journeys_output, BASE_CONFIG)
    df = pd.read_csv(journeys_output)
    complete = df[df["completed"] == True]
    assert (complete["stitch_confidence"] > 0.5).all()
