"""
Reads events.csv, applies the greedy stitching heuristic, writes journeys.csv.

Owns the logic for opening, extending, and closing journeys.
Computes stitch_confidence per journey. Logs orphan event count.

Public API:
    run_stitcher(events_path, output_path, config)
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal

import pandas as pd
from tqdm import tqdm

from src.utils import load_config, setup_logger, timer, write_json

EventType = Literal["entry", "linger", "exit"]


@dataclass(frozen=True, slots=True)
class Event:
    event_id: str
    timestamp: datetime
    zone_id: str
    event_type: EventType
    duration_s: int
    gender: str
    age_range: str


@dataclass(slots=True)
class ActiveJourney:
    journey_id: str
    gender: str
    age_range: str
    start_time: datetime
    last_event_time: datetime
    events: list[Event] = field(default_factory=list)
    zones_visited: list[str] = field(default_factory=list)
    orphan_assignments: int = 0
    max_gap_observed_s: int = 0
    closed_by_exit: bool = False


@dataclass(slots=True)
class Journey:
    journey_id: str
    start_time: datetime
    end_time: datetime
    duration_total_s: int
    n_events: int
    n_zones_visited: int
    zones_sequence: str
    start_zone: str
    end_zone: str
    gender: str
    age_range: str
    completed: bool
    day_of_week: int
    hour_of_day: int
    stitch_confidence: float


def run_stitcher(events_path: str, output_path: str, config: dict) -> None:
    pass


def _load_events(path: str) -> list[Event]:
    pass


def _finalize(active: ActiveJourney, force_closed: bool, config: dict) -> Journey:
    pass


def _compute_confidence(active: ActiveJourney, force_closed: bool, config: dict) -> float:
    pass
