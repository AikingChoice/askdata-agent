# AskData D7 评估报告

> 日期：2026-11-05
> 模型：`deepseek-flash`
> 用例：40（SQL 36，追问/拒答 4）
> EX 定义：候选结果集与 gold 结果集按值多重集比较；浮点保留 2 位，忽略列名与列顺序。
> 投影：`answer_columns` 只比较答案对象列，`answer_index` 只比较指定列（如增长率）；额外证据列不惩罚。

## 1. 总览

| 指标 | 结果 |
|---|---:|
| 路由准确率 | 100.0% |
| Valid SQL Rate | 97.2% |
| Execution Accuracy | 91.7% |
| 追问/拒答正确率 | 100.0% |
| 平均延迟 | 4074 ms |
| p95 延迟 | 8946 ms |
| 修复触发 | 1 例 |
| 修复成功率 | 0.0% |

## 2. 分难度

| 难度 | 用例 | Valid SQL | Execution Accuracy |
|---|---:|---:|---:|
| simple | 12 | 100.0% | 100.0% |
| moderate | 16 | 100.0% | 87.5% |
| challenging | 8 | 87.5% | 87.5% |

## 3. 失败案例

| ID | 问题 | 期望路由 | 实际路由 | Valid | EX | 错误/原因 |
|---|---|---|---|---|---|---|
| Q018 | 各品类毛利率 | sql | sql | True | False | ok |
| Q022 | 上周各区域销售额占比 | sql | sql | True | False | ok |
| Q036 | 连续 3 个月毛利率下降的品类 | sql | sql | False | False | empty SQL |

## 4. 复现

```bash
python scripts/build_golden.py
python scripts/run_eval.py
```

逐例明细见 `data/eval_results.jsonl`，gold SQL 见 `data/golden.jsonl`。
