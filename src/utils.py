"""
Shared utility floor. Keep this under ~80 lines.

Contents:
  load_config(path)    — single source of truth for thresholds
  setup_logger(name)   — writes to file + stdout with timestamped filename
  read_json(path)      — load a JSON file
  write_json(obj, path)— dump with indent=2, sort_keys=True for deterministic diffs
  timer(label)         — context manager that logs elapsed seconds
  validate_schema(obj, schema) — minimal hand-rolled validation
"""

from __future__ import annotations

import json
import logging
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

import yaml


def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r") as fh:
        return yaml.safe_load(fh)


def setup_logger(name: str, log_dir: str = "logs/") -> logging.Logger:
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = Path(log_dir) / f"{name}_{timestamp}.log"

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(fmt)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(fmt)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger


def read_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(obj: dict, path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, sort_keys=True, default=str)


@contextmanager
def timer(label: str, logger: logging.Logger | None = None):
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    msg = f"{label} completed in {elapsed:.2f}s"
    if logger:
        logger.info(msg)
    else:
        print(msg)


def validate_schema(obj: dict, schema: dict) -> list[str]:
    """Return a list of error strings; empty list means valid."""
    errors: list[str] = []
    for key, expected_type in schema.items():
        if key not in obj:
            errors.append(f"Missing key: {key!r}")
        elif not isinstance(obj[key], expected_type):
            errors.append(
                f"Key {key!r}: expected {expected_type.__name__}, "
                f"got {type(obj[key]).__name__}"
            )
    return errors
