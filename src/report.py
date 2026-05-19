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

from src.utils import read_json, setup_logger, timer


def run_report(
    metrics_path: str,
    insights_path: str,
    output_path: str,
    config: dict,
) -> None:
    logger = setup_logger("report", config["paths"]["logs_dir"])

    with timer("load_data", logger):
        metrics = read_json(metrics_path)
        insights = read_json(insights_path)

    templates_dir = config.get("paths", {}).get("templates_dir", "templates/")
    env = Environment(
        loader=FileSystemLoader(str(Path(templates_dir))),
        keep_trailing_newline=True,
    )
    env.globals["resolve"] = _resolve

    template = env.get_template("weekly_report.md.j2")

    with timer("render_template", logger):
        rendered = template.render(metrics=metrics, insights=insights)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    logger.info("Report written to %s", output_path)


def _resolve(metrics: dict, dotted_path: str):
    """Walk a dotted key path into the metrics dict and return the value."""
    node = metrics
    for part in dotted_path.split("."):
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return "N/A"
    return node
