"""Validate schema.sql + seed.sql in an in-memory SQLite database."""

from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "data" / "schema.sql"
SEED = ROOT / "data" / "seed.sql"


def scalar(conn: sqlite3.Connection, sql: str):
    row = conn.execute(sql).fetchone()
    return row[0] if row else None


def rows(conn: sqlite3.Connection, sql: str):
    return conn.execute(sql).fetchall()


def main() -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.executescript(SEED.read_text(encoding="utf-8"))

    print("== row counts ==")
    for table in [
        "dim_dates", "dim_regions", "dim_channels", "dim_products",
        "dim_customers", "dim_campaigns", "dim_sales_reps",
        "fact_orders", "fact_order_items", "fact_refunds",
    ]:
        print(f"{table:20s}", scalar(conn, f"SELECT COUNT(*) FROM {table}"))

    print("\n== foreign key check ==")
    print(rows(conn, "PRAGMA foreign_key_check"))

    print("\n== Q001 Oct 2026 GMV ==")
    print(scalar(conn, """
        SELECT ROUND(SUM(net_amount), 2)
        FROM fact_orders
        WHERE date_id BETWEEN 20261001 AND 20261031
          AND status <> 'cancelled'
    """))

    print("\n== Q002 Oct 2026 net revenue ==")
    print(scalar(conn, """
        SELECT ROUND(
          (SELECT SUM(net_amount) FROM fact_orders
           WHERE date_id BETWEEN 20261001 AND 20261031 AND status <> 'cancelled')
          - COALESCE((SELECT SUM(r.refund_amount)
                      FROM fact_refunds r JOIN fact_orders o ON r.order_id = o.order_id
                      WHERE o.date_id BETWEEN 20261001 AND 20261031
                        AND o.status <> 'cancelled'), 0), 2)
    """))

    print("\n== Q005/Q006 Oct 2026 refund amount / rate ==")
    gmv = scalar(conn, """
        SELECT SUM(net_amount) FROM fact_orders
        WHERE date_id BETWEEN 20261001 AND 20261031 AND status <> 'cancelled'
    """)
    refund = scalar(conn, """
        SELECT SUM(refund_amount) FROM fact_refunds
        WHERE refund_date_id BETWEEN 20261001 AND 20261031
    """)
    print("refund", refund, "gmv", gmv, "rate", round((refund or 0) / (gmv or 1), 4))

    print("\n== Q009 new customers on 2026-11-04 ==")
    print(scalar(conn, "SELECT COUNT(*) FROM dim_customers WHERE register_date_id = 20261104"))

    print("\n== Q013 East Q3 2026 top 10 products ==")
    for row in rows(conn, """
        SELECT p.name, ROUND(SUM(oi.amount), 2) gmv
        FROM fact_orders o
        JOIN fact_order_items oi ON o.order_id = oi.order_id
        JOIN dim_products p ON oi.product_id = p.product_id
        JOIN dim_regions r ON o.region_id = r.region_id
        JOIN dim_dates d ON o.date_id = d.date_id
        WHERE r.region_group = '华东'
          AND d.year_num = 2026 AND d.quarter_num = 3
          AND o.status <> 'cancelled'
        GROUP BY p.product_id, p.name
        ORDER BY gmv DESC
        LIMIT 10
    """):
        print(row)

    print("\n== Q017 Oct 2026 repeat purchase rate ==")
    print(scalar(conn, """
        WITH c AS (
          SELECT customer_id, COUNT(DISTINCT order_id) cnt
          FROM fact_orders
          WHERE date_id BETWEEN 20261001 AND 20261031 AND status <> 'cancelled'
          GROUP BY customer_id
        )
        SELECT ROUND(SUM(CASE WHEN cnt >= 2 THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 4)
        FROM c
    """))

    print("\n== Q019 East Oct 2026 top 5 sales ==")
    for row in rows(conn, """
        SELECT rep.name, ROUND(SUM(o.net_amount), 2) gmv
        FROM fact_orders o
        JOIN dim_sales_reps rep ON o.sales_rep_id = rep.rep_id
        JOIN dim_regions r ON rep.region_id = r.region_id
        WHERE r.region_group = '华东'
          AND o.date_id BETWEEN 20261001 AND 20261031
          AND o.status <> 'cancelled'
        GROUP BY rep.rep_id, rep.name
        ORDER BY gmv DESC
        LIMIT 5
    """):
        print(row)

    print("\n== Q020 Oct 2026 refund reasons ==")
    for row in rows(conn, """
        SELECT COALESCE(reason, 'UNKNOWN') reason, COUNT(*), ROUND(SUM(refund_amount), 2)
        FROM fact_refunds
        WHERE refund_date_id BETWEEN 20261001 AND 20261031
        GROUP BY reason
        ORDER BY 2 DESC
    """):
        print(row)

    print("\n== Q026 East cities Oct 2026 top 5 ==")
    for row in rows(conn, """
        SELECT r.city, COUNT(DISTINCT o.order_id) orders
        FROM fact_orders o JOIN dim_regions r ON o.region_id = r.region_id
        WHERE r.region_group = '华东'
          AND o.date_id BETWEEN 20261001 AND 20261031
          AND o.status <> 'cancelled'
        GROUP BY r.city
        ORDER BY orders DESC
        LIMIT 5
    """):
        print(row)

    print("\n== Q031 Nov 2025 vs Nov 2026 GMV ==")
    for row in rows(conn, """
        SELECT substr(CAST(date_id AS TEXT), 1, 6) ym, ROUND(SUM(net_amount), 2) gmv
        FROM fact_orders
        WHERE ((date_id BETWEEN 20251101 AND 20251130)
            OR (date_id BETWEEN 20261101 AND 20261105))
          AND status <> 'cancelled'
        GROUP BY ym
        ORDER BY ym
    """):
        print(row)

    print("\n== Q030 repeat purchase rate top 3 regions ==")
    for row in rows(conn, """
        WITH c AS (
          SELECT o.customer_id, o.region_id, COUNT(DISTINCT o.order_id) cnt
          FROM fact_orders o
          WHERE o.status <> 'cancelled'
          GROUP BY o.customer_id, o.region_id
        )
        SELECT r.region_group,
               ROUND(SUM(CASE WHEN c.cnt >= 2 THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 4) rate
        FROM c JOIN dim_regions r ON c.region_id = r.region_id
        GROUP BY r.region_group
        ORDER BY rate DESC
        LIMIT 3
    """):
        print(row)

    print("\n== Q033 Oct 2026 top 10 customers: repeat GMV share ==")
    print(scalar(conn, """
        WITH oct AS (
          SELECT customer_id, SUM(net_amount) gmv
          FROM fact_orders
          WHERE date_id BETWEEN 20261001 AND 20261031 AND status <> 'cancelled'
          GROUP BY customer_id
          ORDER BY gmv DESC
          LIMIT 10
        ),
        rep AS (
          SELECT customer_id, COUNT(DISTINCT order_id) cnt
          FROM fact_orders
          WHERE status <> 'cancelled'
          GROUP BY customer_id
        )
        SELECT ROUND(SUM(CASE WHEN rep.cnt >= 2 THEN oct.gmv ELSE 0 END) / SUM(oct.gmv), 4)
        FROM oct JOIN rep ON oct.customer_id = rep.customer_id
    """))

    print("\n== Q029 3-month GMV growth categories ==")
    for row in rows(conn, """
        WITH monthly AS (
          SELECT p.category, d.month_num, SUM(oi.amount) gmv
          FROM fact_orders o
          JOIN fact_order_items oi ON o.order_id = oi.order_id
          JOIN dim_products p ON oi.product_id = p.product_id
          JOIN dim_dates d ON o.date_id = d.date_id
          WHERE o.status <> 'cancelled'
            AND d.year_num = 2026 AND d.month_num BETWEEN 8 AND 10
          GROUP BY p.category, d.month_num
        ),
        piv AS (
          SELECT category,
                 MAX(CASE WHEN month_num = 8 THEN gmv END) m8,
                 MAX(CASE WHEN month_num = 9 THEN gmv END) m9,
                 MAX(CASE WHEN month_num = 10 THEN gmv END) m10
          FROM monthly GROUP BY category
        )
        SELECT category, ROUND(m8, 2), ROUND(m9, 2), ROUND(m10, 2)
        FROM piv WHERE m8 < m9 AND m9 < m10
    """):
        print(row)

    print("\n== Q036 3-month gross margin decline categories ==")
    for row in rows(conn, """
        WITH monthly AS (
          SELECT p.category, d.month_num,
                 SUM(oi.amount) revenue,
                 SUM(oi.quantity * p.cost) cost
          FROM fact_orders o
          JOIN fact_order_items oi ON o.order_id = oi.order_id
          JOIN dim_products p ON oi.product_id = p.product_id
          JOIN dim_dates d ON o.date_id = d.date_id
          WHERE o.status <> 'cancelled'
            AND d.year_num = 2026 AND d.month_num BETWEEN 8 AND 10
          GROUP BY p.category, d.month_num
        ),
        margins AS (
          SELECT category, month_num,
                 (revenue - cost) * 1.0 / NULLIF(revenue, 0) margin
          FROM monthly
        ),
        piv AS (
          SELECT category,
                 MAX(CASE WHEN month_num = 8 THEN margin END) m8,
                 MAX(CASE WHEN month_num = 9 THEN margin END) m9,
                 MAX(CASE WHEN month_num = 10 THEN margin END) m10
          FROM margins GROUP BY category
        )
        SELECT category, ROUND(m8, 4), ROUND(m9, 4), ROUND(m10, 4)
        FROM piv WHERE m8 > m9 AND m9 > m10
    """):
        print(row)

    print("\n== channel order counts ==")
    for row in rows(conn, """
        SELECT COALESCE(c.channel_name, 'UNKNOWN'), COUNT(*) 
        FROM fact_orders o LEFT JOIN dim_channels c ON o.channel_id = c.channel_id
        GROUP BY c.channel_name ORDER BY 2 DESC
    """):
        print(row)

    conn.close()


if __name__ == "__main__":
    main()
