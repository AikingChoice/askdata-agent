from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRACE_PATH = Path(os.getenv("TRACE_LOG_PATH", str(ROOT / "data" / "traces.jsonl")))


def log_trace(question: str, result: dict) -> str:
    trace_id = uuid.uuid4().hex
    analysis = result.get("analysis") or {}
    record = {
        "trace_id": trace_id,
        "ts": time.time(),
        "question": question[:300],
        "route": result.get("route"),
        "analysis": analysis,
        "selected_tables": result.get("selected_tables", []),
        "sql": result.get("sql"),
        "guard_ok": result.get("guard_ok"),
        "row_count": result.get("row_count", 0),
        "attempts": result.get("attempts", 0),
        "trace": result.get("trace", []),
        "latency_ms": result.get("latency_ms", 0),
        "error": result.get("error"),
    }
    if result.get("route") == "refuse" and analysis.get("reason") == "pii":
        record["question"] = "[redacted]"
    try:
        TRACE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with TRACE_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass
    return trace_id
