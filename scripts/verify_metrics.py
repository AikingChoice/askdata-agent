"""Verify D2 metric definitions against the seeded SQLite database.

Usage:
    python scripts/load_db.py --fresh
    python scripts/verify_metrics.py
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "askdata.db"
REPORT = ROOT / "docs" / "metric_validation.md"

MONTH_START = 20261001
MONTH_END = 20261031

QUERIES: list[tuple[str, str, str]] = [
    (
        "GMV（2026-10）",
        "gmv",
        """
        SELECT ROUND(SUM(net_amount), 2) AS gmv
        FROM fact_orders
        WHERE date_id BETWEEN 20261001 AND 20261031
          AND status <> 'cancelled'
        """,
    ),
    (
        "净收入（2026-10）",
        "net_revenue",
        """
        WITH refunds AS (
            SELECT order_id, SUM(refund_amount) AS refund_amount
            FROM fact_refunds
            GROUP BY order_id
        )
        SELECT ROUND(
            SUM(CASE WHEN o.status <> 'cancelled' THEN o.net_amount ELSE 0 END)
            - COALESCE(SUM(r.refund_amount), 0), 2
        ) AS net_revenue
        FROM fact_orders o
        LEFT JOIN refunds r ON r.order_id = o.order_id
        WHERE o.date_id BETWEEN 20261001 AND 20261031
        """,
    ),
    (
        "订单数（2026-10）",
        "order_count",
        """
        SELECT COUNT(DISTINCT order_id) AS order_count
        FROM fact_orders
        WHERE date_id BETWEEN 20261001 AND 20261031
          AND status <> 'cancelled'
        """,
    ),
    (
        "客单价（2026-10）",
        "aov",
        """
        WITH base AS (
            SELECT SUM(net_amount) AS gmv,
                   COUNT(DISTINCT order_id) AS orders
            FROM fact_orders
            WHERE date_id BETWEEN 20261001 AND 20261031
              AND status <> 'cancelled'
        )
        SELECT ROUND(gmv / NULLIF(orders, 0), 2) AS aov
        FROM base
        """,
    ),
    (
        "退款率（按订单归集，2026-10）",
        "refund_rate",
        """
        WITH refunds AS (
            SELECT order_id, SUM(refund_amount) AS refund_amount
            FROM fact_refunds
            GROUP BY order_id
        ),
        gmv AS (
            SELECT SUM(net_amount) AS gmv
            FROM fact_orders
            WHERE date_id BETWEEN 20261001 AND 20261031
              AND status <> 'cancelled'
        ),
        refund AS (
            SELECT SUM(r.refund_amount) AS refund_amount
            FROM fact_orders o
            JOIN refunds r ON r.order_id = o.order_id
            WHERE o.date_id BETWEEN 20261001 AND 20261031
              AND o.status <> 'cancelled'
        )
        SELECT ROUND(COALESCE(refund.refund_amount, 0) / NULLIF(gmv.gmv, 0), 4)
        FROM gmv, refund
        """,
    ),
    (
        "退货率（2026-10）",
        "return_rate",
        """
        WITH paid AS (
            SELECT COUNT(DISTINCT order_id) AS cnt
            FROM fact_orders
            WHERE date_id BETWEEN 20261001 AND 20261031
              AND status <> 'cancelled'
        ),
        refunded AS (
            SELECT COUNT(DISTINCT r.order_id) AS cnt
            FROM fact_refunds r
            JOIN fact_orders o ON o.order_id = r.order_id
            WHERE o.date_id BETWEEN 20261001 AND 20261031
              AND o.status <> 'cancelled'
        )
        SELECT ROUND(refunded.cnt * 1.0 / NULLIF(paid.cnt, 0), 4)
        FROM paid, refunded
        """,
    ),
    (
        "复购率（2026-10）",
        "repeat_purchase_rate",
        """
        WITH customers AS (
            SELECT customer_id, COUNT(DISTINCT order_id) AS cnt
            FROM fact_orders
            WHERE date_id BETWEEN 20261001 AND 20261031
              AND status <> 'cancelled'
            GROUP BY customer_id
        )
        SELECT ROUND(
            SUM(CASE WHEN cnt >= 2 THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 4
        )
        FROM customers
        """,
    ),
    (
        "毛利率（2026-10）",
        "gross_margin",
        """
        WITH refunds AS (
            SELECT order_id, SUM(refund_amount) AS refund_amount
            FROM fact_refunds
            GROUP BY order_id
        ),
        revenue AS (
            SELECT SUM(CASE WHEN o.status <> 'cancelled' THEN o.net_amount ELSE 0 END)
                   - COALESCE(SUM(r.refund_amount), 0) AS revenue
            FROM fact_orders o
            LEFT JOIN refunds r ON r.order_id = o.order_id
            WHERE o.date_id BETWEEN 20261001 AND 20261031
        ),
        cost AS (
            SELECT SUM(oi.quantity * p.cost) AS cost
            FROM fact_orders o
            JOIN fact_order_items oi ON oi.order_id = o.order_id
            JOIN dim_products p ON p.product_id = oi.product_id
            WHERE o.date_id BETWEEN 20261001 AND 20261031
              AND o.status <> 'cancelled'
        )
        SELECT ROUND((revenue.revenue - cost.cost) / NULLIF(revenue.revenue, 0), 4)
        FROM revenue, cost
        """,
    ),
    (
        "退款金额（按退款日期，2026-10）",
        "refund_amount_by_refund_date",
        """
        SELECT ROUND(SUM(refund_amount), 2)
        FROM fact_refunds
        WHERE refund_date_id BETWEEN 20261001 AND 20261031
        """,
    ),
    (
        "昨天新增客户（2026-11-04）",
        "new_customers_yesterday",
        """
        SELECT COUNT(*)
        FROM dim_customers
        WHERE register_date_id = 20261104
        """,
    ),
]


def main() -> None:
    if not DB.exists():
        raise SystemExit(f"DB not found: {DB}. Run python scripts/load_db.py --fresh")

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    fk = conn.execute("PRAGMA foreign_key_check").fetchall()
    results = []
    for label, key, sql in QUERIES:
        value = conn.execute(sql).fetchone()[0]
        results.append((label, key, sql.strip(), value))

    quality = {
        "cancelled_orders": conn.execute(
            "SELECT COUNT(*) FROM fact_orders WHERE status = 'cancelled'"
        ).fetchone()[0],
        "cancelled_net_amount": conn.execute(
            "SELECT ROUND(COALESCE(SUM(net_amount), 0), 2) FROM fact_orders WHERE status = 'cancelled'"
        ).fetchone()[0],
        "null_channel": conn.execute(
            "SELECT COUNT(*) FROM fact_orders WHERE channel_id IS NULL"
        ).fetchone()[0],
        "null_campaign": conn.execute(
            "SELECT COUNT(*) FROM fact_orders WHERE campaign_id IS NULL"
        ).fetchone()[0],
        "null_sales_rep": conn.execute(
            "SELECT COUNT(*) FROM fact_orders WHERE sales_rep_id IS NULL"
        ).fetchone()[0],
        "null_refund_reason": conn.execute(
            "SELECT COUNT(*) FROM fact_refunds WHERE reason IS NULL"
        ).fetchone()[0],
        "east_regions": conn.execute(
            "SELECT COUNT(*) FROM dim_regions WHERE region_group = '华东'"
        ).fetchone()[0],
        "nov_2025_gmv": conn.execute(
            "SELECT ROUND(SUM(net_amount), 2) FROM fact_orders "
            "WHERE date_id BETWEEN 20251101 AND 20251130 AND status <> 'cancelled'"
        ).fetchone()[0],
        "nov_2026_gmv": conn.execute(
            "SELECT ROUND(SUM(net_amount), 2) FROM fact_orders "
            "WHERE date_id BETWEEN 20261101 AND 20261105 AND status <> 'cancelled'"
        ).fetchone()[0],
    }

    by_key = {key: value for _, key, _, value in results}
    checks = {
        "gmv_positive": (by_key["gmv"] or 0) > 0,
        "net_revenue_not_above_gmv": 0 < (by_key["net_revenue"] or 0) <= (by_key["gmv"] or 0),
        "order_count_positive": (by_key["order_count"] or 0) > 0,
        "aov_positive": (by_key["aov"] or 0) > 0,
        "refund_rate_in_range": 0 <= (by_key["refund_rate"] or 0) <= 1,
        "return_rate_in_range": 0 <= (by_key["return_rate"] or 0) <= 1,
        "repeat_rate_in_range": 0 <= (by_key["repeat_purchase_rate"] or 0) <= 1,
        "gross_margin_in_range": -1 <= (by_key["gross_margin"] or 0) <= 1,
        "refund_amount_positive": (by_key["refund_amount_by_refund_date"] or 0) > 0,
        "new_customers_is_3": by_key["new_customers_yesterday"] == 3,
        "foreign_key_check_empty": len(fk) == 0,
    }

    check_by_key = {
        "gmv": "gmv_positive",
        "net_revenue": "net_revenue_not_above_gmv",
        "order_count": "order_count_positive",
        "aov": "aov_positive",
        "refund_rate": "refund_rate_in_range",
        "return_rate": "return_rate_in_range",
        "repeat_purchase_rate": "repeat_rate_in_range",
        "gross_margin": "gross_margin_in_range",
        "refund_amount_by_refund_date": "refund_amount_positive",
        "new_customers_yesterday": "new_customers_is_3",
    }

    lines = [
        "# AskData D2 口径验证",
        "",
        f"> 日期：2026-11-05",
        f"> 数据库：`{DB.relative_to(ROOT).as_posix()}`",
        f"> 验证月份：2026-10",
        "> 说明：所有核心指标按 `fact_orders.date_id`（下单日期）归集，退款按订单归集；退款金额另按 `refund_date_id` 单列。",
        "",
        "## 0. 加载与外键",
        "",
        f"- `PRAGMA foreign_key_check`：`{fk}`",
        "",
        "## 1. 十项基础口径",
        "",
        "| # | 指标 | 结果 | 判断 |",
        "|---:|---|---:|---|",
    ]
    for index, (label, key, _, value) in enumerate(results, start=1):
        status = "PASS" if checks.get(check_by_key.get(key, ""), True) else "CHECK"
        lines.append(f"| {index} | {label} | {value} | {status} |")

    lines += [
        "",
        "## 2. SQL 明细",
        "",
    ]
    for index, (label, key, sql, value) in enumerate(results, start=1):
        lines += [
            f"### {index}. {label}",
            "",
            "```sql",
            sql,
            "```",
            "",
            f"结果：`{value}`",
            "",
        ]

    lines += [
        "## 3. 数据质量检查",
        "",
        "| 检查项 | 值 |",
        "|---|---:|",
    ]
    for key, value in quality.items():
        lines.append(f"| {key} | {value} |")

    lines += [
        "",
        "## 4. 口径结论",
        "",
        "- GMV 排除 `cancelled` 订单；本库取消订单为 "
        f"{quality['cancelled_orders']} 单，金额 {quality['cancelled_net_amount']}，不计入 GMV。",
        "- 净收入使用“先按订单聚合退款、再与订单关联”的两步法，避免一个订单多条退款造成 fan-out 重复计算。",
        "- 退款率按订单归集（退款属于哪张订单，就算到哪个月的 GMV 上）；Q005 的退款金额另按退款日期统计，两者口径不同，不能混用。",
        "- 客单价 = GMV / 订单数，分母是订单数不是客户数。",
        "- 毛利率使用净收入减商品成本；成本来自 `fact_order_items.quantity * dim_products.cost`。",
        "- 复购率按客户聚合订单数，≥2 单算复购；不要把订单行数当订单数。",
        "",
        "## 5. 复现",
        "",
        "```bash",
        "python scripts/load_db.py --fresh",
        "python scripts/verify_metrics.py",
        "```",
        "",
        "## 6. 断言结果",
        "",
        "| 检查 | 结果 |",
        "|---|---|",
    ]
    for key, value in checks.items():
        lines.append(f"| {key} | {'PASS' if value else 'FAIL'} |")

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("== D2 metric verification ==")
    for label, key, _, value in results:
        print(f"{label:28s} {value}")
    print("\nquality:", quality)
    print("checks:", checks)
    print("report:", REPORT)

    failed = [key for key, value in checks.items() if not value]
    if failed:
        raise SystemExit(f"failed checks: {failed}")


if __name__ == "__main__":
    main()
