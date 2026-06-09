from __future__ import annotations

import json
import re
from pathlib import Path

from langchain.tools import tool


METRIC_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_/-]*)\s*=\s*(-?\d+(?:\.\d+)?)")


@tool("log_parser", parse_docstring=True)
def log_parser_tool(path: str | None = None, text: str | None = None, max_lines: int = 400) -> str:
    """Parse a local experiment log for metrics, errors, warnings, and observations.

    Args:
        path: Optional log file path.
        text: Optional raw log text when no path is provided.
        max_lines: Maximum number of trailing log lines to inspect.
    """
    if path is None and text is None:
        raise ValueError("Either path or text is required")

    source_ref = f"log:{Path(path).name}" if path else "log:inline"
    raw_text = Path(path).read_text(encoding="utf-8") if path else text or ""
    lines = raw_text.splitlines()[-max_lines:]

    metrics: dict[str, float] = {}
    errors: list[str] = []
    observations: list[str] = []

    for line in lines:
        stripped = line.strip()
        upper = stripped.upper()
        if "ERROR" in upper or "EXCEPTION" in upper or "TRACEBACK" in upper:
            errors.append(stripped)
        elif "WARN" in upper or "WARNING" in upper:
            observations.append(stripped)

        for key, value in METRIC_RE.findall(stripped):
            metrics[_normalize_metric_name(key)] = float(value)

    payload = {
        "source_ref": source_ref,
        "metrics": metrics,
        "errors": errors,
        "observations": observations,
        "line_count": len(lines),
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def _normalize_metric_name(name: str) -> str:
    normalized = name.lower().replace("-", "_").replace("/", "_")
    if normalized == "acc":
        return "accuracy"
    return normalized
