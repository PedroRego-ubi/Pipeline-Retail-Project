"""
Single-command orchestrator. Runs the full pipeline end-to-end:
  events.csv → stitcher → journeys.csv → analytics → metrics.json
             → insights → insights.json → report → weekly_report.md
             → evaluate → quality_report.json
"""

import sys
import logging
from pathlib import Path

from src.utils import load_config, setup_logger, timer

logger: logging.Logger


def main() -> None:
    config = load_config("config.yaml")
    global logger
    logger = setup_logger("pipeline", config["paths"]["logs_dir"])

    steps = [
        ("stitcher",  _run_stitcher),
        ("analytics", _run_analytics),
        ("insights",  _run_insights),
        ("report",    _run_report),
        ("evaluate",  _run_evaluate),
    ]

    for name, fn in steps:
        with timer(name, logger):
            try:
                fn(config)
            except Exception as exc:
                logger.error("Stage %s failed: %s", name, exc)
                sys.exit(1)

    logger.info("Pipeline complete. Outputs in outputs/")


def _run_stitcher(config: dict) -> None:
    from src.stitcher import run_stitcher
    run_stitcher(
        events_path=config["paths"]["events"],
        output_path=config["paths"]["journeys"],
        config=config,
    )


def _run_analytics(config: dict) -> None:
    from src.analytics import run_analytics
    run_analytics(
        journeys_path=config["paths"]["journeys"],
        output_path=config["paths"]["metrics"],
        config=config,
    )


def _run_insights(config: dict) -> None:
    from src.insights import run_insights
    run_insights(
        metrics_path=config["paths"]["metrics"],
        output_path=config["paths"]["insights"],
        config=config,
    )


def _run_report(config: dict) -> None:
    from src.report import run_report
    run_report(
        metrics_path=config["paths"]["metrics"],
        insights_path=config["paths"]["insights"],
        output_path=config["paths"]["report"],
        config=config,
    )


def _run_evaluate(config: dict) -> None:
    from src.evaluate import run_evaluate
    run_evaluate(
        config=config,
    )


if __name__ == "__main__":
    main()
