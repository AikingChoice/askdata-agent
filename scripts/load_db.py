"""Load AskData schema and seed into data/askdata.db.

Usage:
    python scripts/load_db.py --fresh
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "askdata.db"
SCHEMA = ROOT / "data" / "schema.sql"
SEED = ROOT / "data" / "seed.sql"

TABLES = [
    "dim_dates",
    "dim_regions",
    "dim_channels",
    "dim_products",
    "dim_customers",
    "dim_campaigns",
    "dim_sales_reps",
    "fact_orders",
    "fact_order_items",
    "fact_refunds",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="delete the existing demo DB before loading",
    )
    args = parser.parse_args()

    DB.parent.mkdir(parents=True, exist_ok=True)
    if args.fresh and DB.exists():
        DB.unlink()

    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.executescript(SEED.read_text(encoding="utf-8"))
    conn.commit()

    violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    print("db:", DB)
    print("foreign_key_check:", violations)
    for table in TABLES:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table:20s} {count}")

    conn.close()
    if violations:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
