# AskData D4 Schema 检索评估

> 日期：2026-11-05
> 问题总数：36（有表期望 36，对抗/无表期望跳过 4）
> 方法：keyword baseline / BM25 / BM25 + 外键图

## 1. 汇总

| 方法 | recall@3 | all-hit@3 | recall@5 | all-hit@5 | recall@8 | all-hit@8 |
|---|---:|---:|---:|---:|---:|---:|
| keyword | 89.1% | 63.9% | 95.6% | 83.3% | 96.2% | 86.1% |
| bm25 | 83.4% | 52.8% | 93.3% | 80.6% | 93.8% | 83.3% |
| bm25_fk | 85.3% | 55.6% | 98.3% | 91.7% | 100.0% | 100.0% |

## 2. BM25 + FK 的失败案例（k=8）

无。

## 3. 逐题结果（BM25 + FK, k=8）

| ID | 问题 | 期望 | 召回 | 结果 |
|---|---|---|---|---|
| Q001 | 上月 GMV 是多少？ | fact_orders, dim_dates | dim_dates, fact_orders, fact_refunds, dim_campaigns, dim_customers, fact_order_items, dim_channels, dim_regions | PASS |
| Q002 | 上月净收入是多少？ | fact_orders, fact_refunds, dim_dates | dim_dates, fact_orders, fact_refunds, dim_campaigns, dim_customers, fact_order_items, dim_channels, dim_regions | PASS |
| Q003 | 上周订单数是多少？ | fact_orders, dim_dates | fact_orders, fact_order_items, dim_dates, fact_refunds, dim_campaigns, dim_channels, dim_customers, dim_regions | PASS |
| Q004 | 本月客单价是多少？ | fact_orders, dim_dates | fact_orders, dim_dates, fact_order_items, dim_customers, dim_products, fact_refunds, dim_campaigns, dim_channels | PASS |
| Q005 | 上月退款金额是多少？ | fact_refunds, dim_dates | fact_refunds, dim_dates, fact_orders, fact_order_items, dim_campaigns, dim_customers, dim_channels, dim_regions | PASS |
| Q006 | 上月退款率是多少？ | fact_orders, fact_refunds, dim_dates | fact_orders, fact_refunds, dim_dates, fact_order_items, dim_campaigns, dim_channels, dim_customers, dim_regions | PASS |
| Q007 | 上周各渠道订单数是多少？ | fact_orders, dim_channels, dim_dates | fact_orders, dim_channels, fact_order_items, dim_dates, fact_refunds, dim_campaigns, dim_customers, dim_regions | PASS |
| Q008 | 本月销售额最高的品类是什么？ | fact_orders, fact_order_items, dim_products, dim_dates | fact_order_items, dim_products, fact_orders, dim_sales_reps, dim_dates, dim_campaigns, fact_refunds, dim_channels | PASS |
| Q009 | 昨天新增客户数是多少？ | dim_customers, dim_dates | dim_customers, fact_orders, fact_order_items, dim_dates, dim_regions, fact_refunds, dim_campaigns, dim_channels | PASS |
| Q010 | 上月毛利率是多少？ | fact_orders, fact_order_items, dim_products, fact_refunds, dim_dates | dim_dates, fact_order_items, fact_orders, fact_refunds, dim_campaigns, dim_customers, dim_products, dim_channels | PASS |
| Q011 | 本月至今 GMV 环比上月同期增长率 | fact_orders, dim_dates | dim_dates, fact_orders, dim_products, fact_order_items, dim_customers, fact_refunds, dim_campaigns, dim_channels | PASS |
| Q012 | 上周华东区订单数是多少？ | fact_orders, dim_regions, dim_dates | dim_regions, fact_orders, fact_order_items, dim_dates, dim_sales_reps, dim_customers, fact_refunds, dim_campaigns | PASS |
| Q013 | 华东区 Q3 销售额 top 10 商品 | fact_orders, fact_order_items, dim_products, dim_regions, dim_dates | dim_regions, fact_order_items, dim_sales_reps, fact_orders, dim_products, dim_dates, dim_channels, dim_customers | PASS |
| Q014 | 各区域上月退款率对比 | fact_orders, fact_refunds, dim_regions, dim_dates | fact_orders, dim_dates, fact_refunds, dim_regions, dim_sales_reps, dim_customers, fact_order_items, dim_campaigns | PASS |
| Q015 | 本月 vs 上月 GMV 增长率 | fact_orders, dim_dates | dim_dates, fact_orders, dim_products, fact_order_items, fact_refunds, dim_campaigns, dim_customers, dim_channels | PASS |
| Q016 | 各渠道客单价 | fact_orders, dim_channels | fact_orders, dim_channels, fact_order_items, dim_customers, dim_products, fact_refunds, dim_campaigns, dim_dates | PASS |
| Q017 | 上月复购率是多少？ | fact_orders, dim_customers, dim_dates | dim_dates, dim_customers, fact_orders, fact_refunds, dim_campaigns, dim_regions, fact_order_items, dim_channels | PASS |
| Q018 | 各品类毛利率 | fact_orders, fact_order_items, dim_products, fact_refunds | fact_order_items, dim_products, fact_orders, fact_refunds, dim_campaigns, dim_channels, dim_customers, dim_dates | PASS |
| Q019 | 华东区上月 top 5 销售 by GMV | fact_orders, dim_sales_reps, dim_regions, dim_dates | dim_regions, dim_sales_reps, dim_dates, fact_orders, dim_customers, dim_campaigns, fact_order_items, fact_refunds | PASS |
| Q020 | 上月退款原因分布（按退款单数） | fact_refunds, dim_dates | fact_refunds, fact_orders, dim_dates, fact_order_items, dim_campaigns, dim_channels, dim_customers, dim_regions | PASS |
| Q021 | 本季度各月订单数趋势 | fact_orders, dim_dates | dim_dates, fact_orders, fact_order_items, dim_products, fact_refunds, dim_campaigns, dim_customers, dim_channels | PASS |
| Q022 | 上周各区域销售额占比 | fact_orders, dim_regions, dim_dates | dim_sales_reps, fact_orders, dim_dates, dim_regions, dim_customers, fact_order_items, dim_campaigns, fact_refunds | PASS |
| Q023 | 本月新客 vs 老客 GMV | fact_orders, dim_customers, dim_dates | dim_customers, dim_dates, fact_orders, dim_products, fact_order_items, dim_regions, fact_refunds, dim_campaigns | PASS |
| Q024 | 各渠道退款率 | fact_orders, fact_refunds, dim_channels | fact_orders, dim_channels, fact_refunds, fact_order_items, dim_campaigns, dim_customers, dim_dates, dim_regions | PASS |
| Q025 | 8 月各活动带来的 GMV | fact_orders, dim_campaigns, dim_dates | dim_campaigns, dim_dates, fact_orders, dim_channels, fact_refunds, dim_customers, fact_order_items, dim_regions | PASS |
| Q026 | 华东区各城市订单数 top 5 | fact_orders, dim_regions | dim_regions, fact_orders, fact_order_items, dim_sales_reps, dim_customers, fact_refunds, dim_campaigns, dim_channels | PASS |
| Q027 | 上月退货率最高的品类 | fact_orders, fact_refunds, dim_products, dim_dates | fact_orders, dim_products, dim_dates, fact_order_items, fact_refunds, dim_campaigns, dim_channels, dim_customers | PASS |
| Q028 | 上月毛利率最低的 3 个品类 | fact_orders, fact_order_items, dim_products, fact_refunds, dim_dates | fact_order_items, dim_products, dim_dates, fact_orders, fact_refunds, dim_campaigns, dim_customers, dim_channels | PASS |
| Q029 | 8-10 月连续 3 个月 GMV 增长的品类 | fact_orders, fact_order_items, dim_products, dim_dates | dim_products, dim_dates, fact_order_items, fact_orders, fact_refunds, dim_campaigns, dim_customers, dim_channels | PASS |
| Q030 | 各区域复购率 | fact_orders, dim_customers, dim_regions | dim_customers, fact_orders, dim_regions, dim_sales_reps, dim_dates, fact_order_items, fact_refunds, dim_campaigns | PASS |
| Q031 | 本月 GMV 同比去年同月 | fact_orders, dim_dates | dim_dates, fact_orders, dim_campaigns, dim_products, fact_order_items, fact_refunds, dim_customers, dim_channels | PASS |
| Q032 | 10 月和 11 月各区域退款率（返回两个月退款率） | fact_orders, fact_refunds, dim_regions, dim_dates | fact_orders, fact_refunds, dim_dates, dim_regions, dim_sales_reps, dim_customers, dim_campaigns, fact_order_items | PASS |
| Q033 | 上月 top 10 客户中复购客户的 GMV 占比 | fact_orders, dim_customers, dim_dates | dim_customers, dim_dates, fact_orders, dim_regions, fact_refunds, dim_campaigns, fact_order_items, dim_channels | PASS |
| Q034 | 各渠道客单价中位数 | fact_orders, dim_channels | fact_orders, dim_channels, fact_order_items, dim_customers, dim_products, fact_refunds, dim_campaigns, dim_dates | PASS |
| Q035 | 上月退货率高于全店平均的品类 | fact_orders, fact_refunds, dim_products, dim_dates | fact_orders, dim_products, dim_dates, fact_order_items, fact_refunds, dim_channels, dim_campaigns, dim_customers | PASS |
| Q036 | 连续 3 个月毛利率下降的品类 | fact_orders, fact_order_items, dim_products, fact_refunds, dim_dates | fact_order_items, dim_products, fact_orders, dim_dates, dim_channels, fact_refunds, dim_campaigns, dim_customers | PASS |
