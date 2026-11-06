from __future__ import annotations

from pathlib import Path

import yaml


def load_metrics(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def format_metrics(data: dict) -> str:
    lines: list[str] = []
    for key, metric in data.get("metrics", {}).items():
        synonyms = ", ".join(metric.get("synonyms", []))
        lines.append(
            f"- {metric.get('label', key)} ({key}): {metric.get('definition', '')} "
            f"| formula: {metric.get('formula', '')} | synonyms: {synonyms}"
        )
    for key, metric in data.get("derived_metrics", {}).items():
        synonyms = ", ".join(metric.get("synonyms", []))
        lines.append(
            f"- [derived] {metric.get('label', key)} ({key}): {metric.get('definition', '')} "
            f"| formula: {metric.get('formula', '')} | synonyms: {synonyms}"
        )
    for item in data.get("ambiguities", []):
        lines.append(
            f"- ambiguity: {item['term']} default={item['default']} "
            f"alternatives={item['alternatives']}"
        )
    return "\n".join(lines)
