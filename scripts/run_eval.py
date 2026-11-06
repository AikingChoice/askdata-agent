"""D7: run the 40-case golden set against the live AskData pipeline."""

from __future__ import annotations

import json
import time
from pathlib import Path

from app.config import Settings
from app.executor import execute_readonly
from app.llm import build_llm
from app.metrics import load_metrics
from app.pipeline import AskPipeline
from app.schema_catalog import load_schema

ROOT = Path(__file__).resolve().parent.parent
GOLDEN = ROOT / "data" / "golden.jsonl"
RESULTS = ROOT / "data" / "eval_results.jsonl"
REPORT = ROOT / "docs" / "eval_report.md"


def canonical(rows: list[dict]) -> list[tuple]:
    result = []
    for row in rows:
        values = []
        for value in row.values():
            if value is None:
                values.append("NULL")
            elif isinstance(value, float):
                values.append(round(value, 2))
            else:
                values.append(str(value).strip())
        result.append(tuple(sorted(values, key=str)))
    return sorted(result, key=lambda item: tuple(map(str, item)))


def project_rows(rows: list[dict], case: dict) -> list[dict] | None:
    ignore_null = case.get("ignore_null_columns") or []
    if ignore_null:
        rows = [
            row
            for row in rows
            if all(row.get(column) is not None for column in ignore_null)
        ]
    index = case.get("answer_index")
    columns = case.get("answer_columns")
    if index is not None:
        projected = []
        for row in rows:
            value = list(row.values())[index]
            if value is not None:
                projected.append({"answer": value})
        return projected
    if columns:
        projected = []
        for row in rows:
            if not all(column in row for column in columns):
                return None
            projected.append({column: row[column] for column in columns})
        return projected
    return rows


def p95(values: list[int]) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(len(ordered) * 0.95))
    return ordered[index]


def main() -> None:
    cases = [
        json.loads(line)
        for line in GOLDEN.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    settings = Settings()
    pipeline = AskPipeline(
        settings,
        load_schema(settings.db_path),
        load_metrics(settings.metrics_path),
        build_llm(settings),
    )

    results = []
    for index, case in enumerate(cases, start=1):
        started = time.perf_counter()
        response = pipeline.ask(case["question"])
        latency = int((time.perf_counter() - started) * 1000)
        expected_route = case["expected_route"]
        route_ok = response.get("route") == expected_route

        if expected_route != "sql":
            passed = route_ok and bool(response.get("answer"))
            results.append(
                {
                    "id": case["id"],
                    "question": case["question"],
                    "difficulty": case["difficulty"],
                    "expected_route": expected_route,
                    "actual_route": response.get("route"),
                    "route_ok": route_ok,
                    "valid_sql": None,
                    "exec_match": None,
                    "passed": passed,
                    "attempts": response.get("attempts", 0),
                    "latency_ms": latency,
                    "answer": response.get("answer", ""),
                    "analysis": response.get("analysis", {}),
                }
            )
            print(f"{index:02d}/{len(cases)} {case['id']} route={response.get('route')}")
            continue

        valid_sql = bool(response.get("guard_ok")) and response.get("error") is None
        gold = execute_readonly(
            settings.db_path, case["gold_sql"], max_rows=1000
        )
        gold_rows = gold.rows
        candidate_rows = response.get("rows", [])
        candidate_projected = project_rows(candidate_rows, case)
        gold_projected = project_rows(gold_rows, case)
        exec_match = bool(
            valid_sql
            and candidate_projected is not None
            and gold_projected is not None
            and canonical(candidate_projected) == canonical(gold_projected)
        )
        passed = bool(route_ok and valid_sql and exec_match)

        results.append(
            {
                "id": case["id"],
                "question": case["question"],
                "difficulty": case["difficulty"],
                "expected_route": expected_route,
                "actual_route": response.get("route"),
                "route_ok": route_ok,
                "valid_sql": valid_sql,
                "exec_match": exec_match,
                "passed": passed,
                "attempts": response.get("attempts", 0),
                "latency_ms": latency,
                "sql": response.get("sql"),
                "raw_sql": response.get("raw_sql"),
                "gold_sql": case["gold_sql"],
                "candidate_rows": candidate_rows,
                "gold_rows": gold_rows,
                "columns": response.get("columns", []),
                "error": response.get("error") or response.get("guard_reason"),
                "trace": response.get("trace", []),
            }
        )
        print(
            f"{index:02d}/{len(cases)} {case['id']} "
            f"route={response.get('route')} valid={valid_sql} ex={exec_match} "
            f"attempts={response.get('attempts', 0)}"
        )

    sql_cases = [item for item in results if item["expected_route"] == "sql"]
    non_sql_cases = [item for item in results if item["expected_route"] != "sql"]
    route_accuracy = sum(item["route_ok"] for item in results) / len(results)
    valid_sql_rate = sum(item["valid_sql"] for item in sql_cases) / len(sql_cases)
    execution_accuracy = sum(item["exec_match"] for item in sql_cases) / len(sql_cases)
    refusal_correctness = (
        sum(item["passed"] for item in non_sql_cases) / len(non_sql_cases)
        if non_sql_cases
        else 1.0
    )
    latencies = [item["latency_ms"] for item in results]
    repaired = [item for item in results if item["attempts"] > 1]
    repair_success = (
        sum(item["passed"] for item in repaired) / len(repaired) if repaired else 1.0
    )

    by_difficulty = {}
    for difficulty in ("simple", "moderate", "challenging"):
        subset = [item for item in sql_cases if item["difficulty"] == difficulty]
        by_difficulty[difficulty] = {
            "count": len(subset),
            "execution_accuracy": (
                sum(item["exec_match"] for item in subset) / len(subset)
                if subset
                else 0.0
            ),
            "valid_sql_rate": (
                sum(item["valid_sql"] for item in subset) / len(subset)
                if subset
                else 0.0
            ),
        }

    RESULTS.write_text(
        "\n".join(json.dumps(item, ensure_ascii=False) for item in results) + "\n",
        encoding="utf-8",
    )

    failures = [item for item in results if not item["passed"]]
    lines = [
        "# AskData D7 评估报告",
        "",
        f"> 日期：2026-11-05",
        f"> 模型：`{getattr(pipeline.llm, 'model', 'unknown')}`",
        f"> 用例：{len(results)}（SQL {len(sql_cases)}，追问/拒答 {len(non_sql_cases)}）",
        "> EX 定义：候选结果集与 gold 结果集按值多重集比较；浮点保留 2 位，忽略列名与列顺序。",
        "> 投影：`answer_columns` 只比较答案对象列，`answer_index` 只比较指定列（如增长率）；额外证据列不惩罚。",
        "",
        "## 1. 总览",
        "",
        "| 指标 | 结果 |",
        "|---|---:|",
        f"| 路由准确率 | {route_accuracy:.1%} |",
        f"| Valid SQL Rate | {valid_sql_rate:.1%} |",
        f"| Execution Accuracy | {execution_accuracy:.1%} |",
        f"| 追问/拒答正确率 | {refusal_correctness:.1%} |",
        f"| 平均延迟 | {sum(latencies) / len(latencies):.0f} ms |",
        f"| p95 延迟 | {p95(latencies)} ms |",
        f"| 修复触发 | {len(repaired)} 例 |",
        f"| 修复成功率 | {repair_success:.1%} |",
        "",
        "## 2. 分难度",
        "",
        "| 难度 | 用例 | Valid SQL | Execution Accuracy |",
        "|---|---:|---:|---:|",
    ]
    for difficulty, metrics in by_difficulty.items():
        lines.append(
            f"| {difficulty} | {metrics['count']} | "
            f"{metrics['valid_sql_rate']:.1%} | {metrics['execution_accuracy']:.1%} |"
        )

    lines += [
        "",
        "## 3. 失败案例",
        "",
    ]
    if not failures:
        lines.append("无。")
    else:
        lines += [
            "| ID | 问题 | 期望路由 | 实际路由 | Valid | EX | 错误/原因 |",
            "|---|---|---|---|---|---|---|",
        ]
        for item in failures:
            reason = item.get("error") or "result mismatch"
            lines.append(
                f"| {item['id']} | {item['question']} | {item['expected_route']} | "
                f"{item['actual_route']} | {item.get('valid_sql')} | "
                f"{item.get('exec_match')} | {reason} |"
            )

    lines += [
        "",
        "## 4. 复现",
        "",
        "```bash",
        "python scripts/build_golden.py",
        "python scripts/run_eval.py",
        "```",
        "",
        "逐例明细见 `data/eval_results.jsonl`，gold SQL 见 `data/golden.jsonl`。",
    ]

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("\n== D7 summary ==")
    print(f"route_accuracy={route_accuracy:.1%}")
    print(f"valid_sql_rate={valid_sql_rate:.1%}")
    print(f"execution_accuracy={execution_accuracy:.1%}")
    print(f"refusal_correctness={refusal_correctness:.1%}")
    print(f"repaired={len(repaired)} repair_success={repair_success:.1%}")
    print(f"avg_latency={sum(latencies) / len(latencies):.0f}ms p95={p95(latencies)}ms")
    print("by_difficulty:", json.dumps(by_difficulty, ensure_ascii=False))
    print("report:", REPORT)

    if route_accuracy < 0.95 or refusal_correctness < 0.9:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
