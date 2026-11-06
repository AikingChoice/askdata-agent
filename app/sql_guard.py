from __future__ import annotations

import re
from dataclasses import dataclass, field

import sqlglot
from sqlglot import exp

FORBIDDEN_KEYS = {
    "insert",
    "update",
    "delete",
    "drop",
    "create",
    "alter",
    "command",
    "attach",
    "detach",
    "pragma",
    "transaction",
    "into",
    "use",
    "grant",
    "revoke",
    "copy",
    "merge",
}


@dataclass
class GuardResult:
    ok: bool
    sql: str | None = None
    reason: str = ""
    tables: list[str] = field(default_factory=list)


def guard_sql(
    sql: str,
    allowed_tables: set[str],
    max_rows: int = 1000,
) -> GuardResult:
    raw = (sql or "").strip()
    if not raw:
        return GuardResult(False, reason="empty SQL")
    if "--" in raw or "/*" in raw:
        return GuardResult(False, reason="SQL comments are not allowed")

    try:
        statements = [
            statement
            for statement in sqlglot.parse(raw, read="sqlite")
            if statement is not None
        ]
    except Exception as exc:
        return GuardResult(False, reason=f"SQL parse error: {exc}")

    if len(statements) != 1:
        return GuardResult(False, reason="only a single statement is allowed")

    tree = statements[0]
    if not isinstance(tree, exp.Select):
        return GuardResult(False, reason="only SELECT is allowed")

    cte_names: set[str] = set()
    for cte in tree.find_all(exp.CTE):
        alias = getattr(cte, "alias_or_name", "") or getattr(cte, "alias", "")
        if alias:
            cte_names.add(alias.lower())

    allowed = {name.lower() for name in allowed_tables}
    used: list[str] = []
    for node in tree.walk():
        key = getattr(node, "key", "")
        if key in FORBIDDEN_KEYS:
            return GuardResult(False, reason=f"forbidden SQL construct: {key}")
        if isinstance(node, exp.Table):
            name = (node.name or "").lower()
            if not name:
                return GuardResult(False, reason="table name is missing")
            if node.db or node.catalog:
                return GuardResult(False, reason="qualified table names are not allowed")
            if name in cte_names:
                continue
            if name not in allowed:
                return GuardResult(False, reason=f"table not allowed: {name}")
            if name not in used:
                used.append(name)

    try:
        limit = tree.args.get("limit")
        if limit is None:
            tree = tree.limit(max_rows)
        else:
            try:
                current_limit = int(limit.expression.this)
            except (TypeError, ValueError):
                current_limit = max_rows + 1
            if current_limit > max_rows:
                tree = tree.limit(max_rows)
    except Exception as exc:
        return GuardResult(False, reason=f"failed to apply row limit: {exc}")

    return GuardResult(
        True,
        sql=tree.sql(dialect="sqlite"),
        reason="ok",
        tables=used,
    )
