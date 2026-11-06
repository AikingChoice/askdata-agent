from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ExecResult:
    ok: bool
    columns: list[str] = field(default_factory=list)
    rows: list[dict] = field(default_factory=list)
    truncated: bool = False
    error: str | None = None
    elapsed_ms: int = 0


def execute_readonly(
    db_path: Path,
    sql: str,
    max_rows: int = 200,
    timeout_ms: int = 3000,
) -> ExecResult:
    started = time.perf_counter()
    if not db_path.exists():
        return ExecResult(False, error=f"database not found: {db_path}")

    uri = f"file:{db_path.as_posix()}?mode=ro"
    conn: sqlite3.Connection | None = None
    try:
        conn = sqlite3.connect(uri, uri=True, timeout=timeout_ms / 1000)
        conn.execute("PRAGMA query_only = ON")
        deadline = time.monotonic() + timeout_ms / 1000

        def watchdog() -> int:
            return 1 if time.monotonic() > deadline else 0

        conn.set_progress_handler(watchdog, 1000)
        cursor = conn.execute(sql)
        columns = [item[0] for item in (cursor.description or [])]
        fetched = cursor.fetchmany(max_rows + 1)
        truncated = len(fetched) > max_rows
        fetched = fetched[:max_rows]
        rows = [dict(zip(columns, row)) for row in fetched]
        return ExecResult(
            True,
            columns=columns,
            rows=rows,
            truncated=truncated,
            elapsed_ms=int((time.perf_counter() - started) * 1000),
        )
    except sqlite3.Error as exc:
        message = str(exc)
        if "interrupted" in message.lower():
            message = "query timeout"
        return ExecResult(
            False,
            error=message,
            elapsed_ms=int((time.perf_counter() - started) * 1000),
        )
    finally:
        if conn is not None:
            conn.close()
