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

from src.utils import load_config, setup_logger, timer

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
    logger = setup_logger("stitcher", config["paths"]["logs_dir"])

    stitcher_cfg = config["stitcher"]
    max_gap_s: int = stitcher_cfg["max_gap_s"]
    max_journey_s: int = stitcher_cfg["max_journey_s"]

    with timer("Load events", logger):
        events = _load_events(events_path)

    logger.info(f"Loaded {len(events):,} events")

    # Bucketed by (gender, age_range) — O(1) lookup per event
    active_pool: dict[tuple[str, str], list[ActiveJourney]] = defaultdict(list)
    journeys: list[Journey] = []
    journey_counter = 0
    orphan_count = 0
    total_eligible = 0
    total_linger_exit = 0

    def _next_id() -> str:
        nonlocal journey_counter
        journey_counter += 1
        return f"J{journey_counter:06d}"

    def _force_close_stale(current_time: datetime) -> None:
        for bucket in active_pool.values():
            stale = [
                j for j in bucket
                if (current_time - j.start_time).total_seconds() > max_journey_s
            ]
            for j in stale:
                journeys.append(_finalize(j, force_closed=True, config=config))
                bucket.remove(j)

    with timer("Stitch events", logger):
        for event in tqdm(events, desc="Stitching", unit="evt"):
            _force_close_stale(event.timestamp)

            key = (event.gender, event.age_range)

            if event.event_type == "entry":
                j = ActiveJourney(
                    journey_id=_next_id(),
                    gender=event.gender,
                    age_range=event.age_range,
                    start_time=event.timestamp,
                    last_event_time=event.timestamp,
                    events=[event],
                    zones_visited=[event.zone_id],
                )
                active_pool[key].append(j)

            else:  # linger or exit
                bucket = active_pool[key]
                eligible = [
                    j for j in bucket
                    if (event.timestamp - j.last_event_time).total_seconds() <= max_gap_s
                ]

                total_linger_exit += 1
                total_eligible += len(eligible)

                if eligible:
                    # Assign to oldest open match (earliest start_time)
                    target = min(eligible, key=lambda j: j.start_time)

                    gap_s = int((event.timestamp - target.last_event_time).total_seconds())
                    if gap_s > target.max_gap_observed_s:
                        target.max_gap_observed_s = gap_s

                    if not target.zones_visited or target.zones_visited[-1] != event.zone_id:
                        target.zones_visited.append(event.zone_id)

                    target.last_event_time = event.timestamp
                    target.events.append(event)

                    if event.event_type == "exit":
                        target.closed_by_exit = True
                        bucket.remove(target)
                        journeys.append(_finalize(target, force_closed=False, config=config))

                else:
                    # Orphan: synthesize a new low-confidence journey
                    orphan_count += 1
                    j = ActiveJourney(
                        journey_id=_next_id(),
                        gender=event.gender,
                        age_range=event.age_range,
                        start_time=event.timestamp,
                        last_event_time=event.timestamp,
                        events=[event],
                        zones_visited=[event.zone_id],
                        orphan_assignments=1,
                    )
                    if event.event_type == "exit":
                        j.closed_by_exit = True
                        journeys.append(_finalize(j, force_closed=False, config=config))
                    else:
                        active_pool[key].append(j)

    # Force-close every journey still open at end of stream
    for bucket in active_pool.values():
        for j in list(bucket):
            journeys.append(_finalize(j, force_closed=True, config=config))

    bucket_collision_rate = (
        total_eligible / total_linger_exit if total_linger_exit > 0 else 0.0
    )
    orphan_rate = orphan_count / len(events) if events else 0.0

    logger.info(f"Journeys produced:      {len(journeys):,}")
    logger.info(f"Orphan events:          {orphan_count:,} ({orphan_rate:.1%} of events)")
    logger.info(f"Bucket collision rate:  {bucket_collision_rate:.2f}")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    rows = [
        {
            "journey_id": j.journey_id,
            "start_time": j.start_time,
            "end_time": j.end_time,
            "duration_total_s": j.duration_total_s,
            "n_events": j.n_events,
            "n_zones_visited": j.n_zones_visited,
            "zones_sequence": j.zones_sequence,
            "start_zone": j.start_zone,
            "end_zone": j.end_zone,
            "gender": j.gender,
            "age_range": j.age_range,
            "completed": j.completed,
            "day_of_week": j.day_of_week,
            "hour_of_day": j.hour_of_day,
            "stitch_confidence": j.stitch_confidence,
        }
        for j in journeys
    ]

    pd.DataFrame(rows).to_csv(output_path, index=False)
    logger.info(f"Wrote {len(rows):,} rows to {output_path}")


def _load_events(path: str) -> list[Event]:
    df = pd.read_csv(path, parse_dates=["timestamp"])
    df.sort_values("timestamp", inplace=True, ignore_index=True)
    return [
        Event(
            event_id=str(row.event_id),
            timestamp=row.timestamp.to_pydatetime(),
            zone_id=str(row.zone_id),
            event_type=row.event_type,
            duration_s=int(row.duration_s),
            gender=str(row.gender),
            age_range=str(row.age_range),
        )
        for row in df.itertuples(index=False)
    ]


def _finalize(active: ActiveJourney, force_closed: bool, config: dict) -> Journey:
    confidence = _compute_confidence(active, force_closed, config)
    return Journey(
        journey_id=active.journey_id,
        start_time=active.start_time,
        end_time=active.last_event_time,
        duration_total_s=int(
            (active.last_event_time - active.start_time).total_seconds()
        ),
        n_events=len(active.events),
        n_zones_visited=len(set(active.zones_visited)),
        zones_sequence=";".join(active.zones_visited),
        start_zone=active.zones_visited[0],
        end_zone=active.zones_visited[-1],
        gender=active.gender,
        age_range=active.age_range,
        completed=not force_closed,
        day_of_week=active.start_time.weekday(),
        hour_of_day=active.start_time.hour,
        stitch_confidence=confidence,
    )


def _compute_confidence(active: ActiveJourney, force_closed: bool, config: dict) -> float:
    cfg = config["stitcher"]["confidence"]
    max_gap_s: int = config["stitcher"]["max_gap_s"]
    score = 1.0
    score -= cfg["orphan_penalty"] * active.orphan_assignments
    if force_closed:
        score -= cfg["no_exit_penalty"]
    if active.max_gap_observed_s > cfg["near_threshold_gap_ratio"] * max_gap_s:
        score -= cfg["near_threshold_gap_penalty"]
    return max(0.0, min(1.0, score))


if __name__ == "__main__":
    cfg = load_config()
    run_stitcher(cfg["paths"]["events"], cfg["paths"]["journeys"], cfg)
