# AskData D2 口径验证

> 日期：2026-11-05
> 数据库：`data/askdata.db`
> 验证月份：2026-10
> 说明：所有核心指标按 `fact_orders.date_id`（下单日期）归集，退款按订单归集；退款金额另按 `refund_date_id` 单列。

## 0. 加载与外键

- `PRAGMA foreign_key_check`：`[]`

## 1. 十项基础口径

| # | 指标 | 结果 | 判断 |
|---:|---|---:|---|
| 1 | GMV（2026-10） | 61609.57 | PASS |
| 2 | 净收入（2026-10） | 58208.56 | PASS |
| 3 | 订单数（2026-10） | 50 | PASS |
| 4 | 客单价（2026-10） | 1232.19 | PASS |
| 5 | 退款率（按订单归集，2026-10） | 0.0552 | PASS |
| 6 | 退货率（2026-10） | 0.16 | PASS |
| 7 | 复购率（2026-10） | 0.56 | PASS |
| 8 | 毛利率（2026-10） | 0.4718 | PASS |
| 9 | 退款金额（按退款日期，2026-10） | 2542.27 | PASS |
| 10 | 昨天新增客户（2026-11-04） | 3 | PASS |

## 2. SQL 明细

### 1. GMV（2026-10）

```sql
SELECT ROUND(SUM(net_amount), 2) AS gmv
        FROM fact_orders
        WHERE date_id BETWEEN 20261001 AND 20261031
          AND status <> 'cancelled'
```

结果：`61609.57`

### 2. 净收入（2026-10）

```sql
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
```

结果：`58208.56`

### 3. 订单数（2026-10）

```sql
SELECT COUNT(DISTINCT order_id) AS order_count
        FROM fact_orders
        WHERE date_id BETWEEN 20261001 AND 20261031
          AND status <> 'cancelled'
```

结果：`50`

### 4. 客单价（2026-10）

```sql
WITH base AS (
            SELECT SUM(net_amount) AS gmv,
                   COUNT(DISTINCT order_id) AS orders
            FROM fact_orders
            WHERE date_id BETWEEN 20261001 AND 20261031
              AND status <> 'cancelled'
        )
        SELECT ROUND(gmv / NULLIF(orders, 0), 2) AS aov
        FROM base
```

结果：`1232.19`

### 5. 退款率（按订单归集，2026-10）

```sql
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
```

结果：`0.0552`

### 6. 退货率（2026-10）

```sql
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
```

结果：`0.16`

### 7. 复购率（2026-10）

```sql
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
```

结果：`0.56`

### 8. 毛利率（2026-10）

```sql
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
```

结果：`0.4718`

### 9. 退款金额（按退款日期，2026-10）

```sql
SELECT ROUND(SUM(refund_amount), 2)
        FROM fact_refunds
        WHERE refund_date_id BETWEEN 20261001 AND 20261031
```

结果：`2542.27`

### 10. 昨天新增客户（2026-11-04）

```sql
SELECT COUNT(*)
        FROM dim_customers
        WHERE register_date_id = 20261104
```

结果：`3`

## 3. 数据质量检查

| 检查项 | 值 |
|---|---:|
| cancelled_orders | 12 |
| cancelled_net_amount | 14580.16 |
| null_channel | 17 |
| null_campaign | 374 |
| null_sales_rep | 40 |
| null_refund_reason | 13 |
| east_regions | 6 |
| nov_2025_gmv | 38711.85 |
| nov_2026_gmv | 24989.88 |

## 4. 口径结论

- GMV 排除 `cancelled` 订单；本库取消订单为 12 单，金额 14580.16，不计入 GMV。
- 净收入使用“先按订单聚合退款、再与订单关联”的两步法，避免一个订单多条退款造成 fan-out 重复计算。
- 退款率按订单归集（退款属于哪张订单，就算到哪个月的 GMV 上）；Q005 的退款金额另按退款日期统计，两者口径不同，不能混用。
- 客单价 = GMV / 订单数，分母是订单数不是客户数。
- 毛利率使用净收入减商品成本；成本来自 `fact_order_items.quantity * dim_products.cost`。
- 复购率按客户聚合订单数，≥2 单算复购；不要把订单行数当订单数。

## 5. 复现

```bash
python scripts/load_db.py --fresh
python scripts/verify_metrics.py
```

## 6. 断言结果

| 检查 | 结果 |
|---|---|
| gmv_positive | PASS |
| net_revenue_not_above_gmv | PASS |
| order_count_positive | PASS |
| aov_positive | PASS |
| refund_rate_in_range | PASS |
| return_rate_in_range | PASS |
| repeat_rate_in_range | PASS |
| gross_margin_in_range | PASS |
| refund_amount_positive | PASS |
| new_customers_is_3 | PASS |
| foreign_key_check_empty | PASS |
