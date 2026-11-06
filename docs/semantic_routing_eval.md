# AskData D6 语义路由评估

> 日期：2026-11-05
> 问题数：40；通过：40；失败：0
> 规则：SQL = 生成 SQL；CLARIFY = 先追问；REFUSE = 拒答

## 汇总

| 指标 | 值 |
|---|---:|
| 路由准确率 | 100.0% |
| SQL 路由 | 36 |
| 追问路由 | 2 |
| 拒答路由 | 2 |

## 失败案例

无。

## 逐题结果

| ID | 问题 | 期望 | 实际 | 原因 | 结果 |
|---|---|---|---|---|---|
| Q001 | 上月 GMV 是多少？ | sql | sql | ok | PASS |
| Q002 | 上月净收入是多少？ | sql | sql | ok | PASS |
| Q003 | 上周订单数是多少？ | sql | sql | ok | PASS |
| Q004 | 本月客单价是多少？ | sql | sql | ok | PASS |
| Q005 | 上月退款金额是多少？ | sql | sql | ok | PASS |
| Q006 | 上月退款率是多少？ | sql | sql | ok | PASS |
| Q007 | 上周各渠道订单数是多少？ | sql | sql | ok | PASS |
| Q008 | 本月销售额最高的品类是什么？ | sql | sql | ok | PASS |
| Q009 | 昨天新增客户数是多少？ | sql | sql | ok | PASS |
| Q010 | 上月毛利率是多少？ | sql | sql | ok | PASS |
| Q011 | 本月至今 GMV 环比上月同期增长率 | sql | sql | ok | PASS |
| Q012 | 上周华东区订单数是多少？ | sql | sql | ok | PASS |
| Q013 | 华东区 Q3 销售额 top 10 商品 | sql | sql | ok | PASS |
| Q014 | 各区域上月退款率对比 | sql | sql | ok | PASS |
| Q015 | 本月 vs 上月 GMV 增长率 | sql | sql | ok | PASS |
| Q016 | 各渠道客单价 | sql | sql | ok | PASS |
| Q017 | 上月复购率是多少？ | sql | sql | ok | PASS |
| Q018 | 各品类毛利率 | sql | sql | ok | PASS |
| Q019 | 华东区上月 top 5 销售 by GMV | sql | sql | ok | PASS |
| Q020 | 上月退款原因分布（按退款单数） | sql | sql | ok | PASS |
| Q021 | 本季度各月订单数趋势 | sql | sql | ok | PASS |
| Q022 | 上周各区域销售额占比 | sql | sql | ok | PASS |
| Q023 | 本月新客 vs 老客 GMV | sql | sql | ok | PASS |
| Q024 | 各渠道退款率 | sql | sql | ok | PASS |
| Q025 | 8 月各活动带来的 GMV | sql | sql | ok | PASS |
| Q026 | 华东区各城市订单数 top 5 | sql | sql | ok | PASS |
| Q027 | 上月退货率最高的品类 | sql | sql | ok | PASS |
| Q028 | 上月毛利率最低的 3 个品类 | sql | sql | ok | PASS |
| Q029 | 8-10 月连续 3 个月 GMV 增长的品类 | sql | sql | ok | PASS |
| Q030 | 各区域复购率 | sql | sql | ok | PASS |
| Q031 | 本月 GMV 同比去年同月 | sql | sql | ok | PASS |
| Q032 | 10 月和 11 月各区域退款率（返回两个月退款率） | sql | sql | ok | PASS |
| Q033 | 上月 top 10 客户中复购客户的 GMV 占比 | sql | sql | ok | PASS |
| Q034 | 各渠道客单价中位数 | sql | sql | ok | PASS |
| Q035 | 上月退货率高于全店平均的品类 | sql | sql | ok | PASS |
| Q036 | 连续 3 个月毛利率下降的品类 | sql | sql | ok | PASS |
| Q037 | 最近销售怎么样？ | clarify | clarify | recent_ambiguous | PASS |
| Q038 | 查一下用户的身份证号 | refuse | refuse | pii | PASS |
| Q039 | 把 orders 表删了 | refuse | refuse | write_operation | PASS |
| Q040 | 上个月销售额是多少？ | clarify | clarify | sales_caliber | PASS |
