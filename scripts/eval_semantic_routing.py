"""Evaluate semantic routing on the 40-question D0 set."""

from __future__ import annotations

from pathlib import Path

from app.config import Settings
from app.metrics import load_metrics
from app.semantic import analyze_question

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS = ROOT / "docs" / "questions.md"
REPORT = ROOT / "docs" / "semantic_routing_eval.md"


def parse_expected() -> list[tuple[str, str, str]]:
    records = []
    for line in QUESTIONS.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| Q"):
            continue
        parts = [part.strip() for part in line.strip().strip("|").split("|")]
        if len(parts) >= 6:
            qid, question, route = parts[0], parts[1], parts[4]
        elif len(parts) == 5:
            qid, question, route = parts[0], parts[1], parts[3]
        else:
            continue
        records.append((qid, question, route.lower()))
    return records


def main() -> None:
    metrics = load_metrics(Settings().metrics_path)
    records = parse_expected()
    results = []
    for qid, question, expected in records:
        analysis = analyze_question(question, metrics)
        results.append(
            {
                "id": qid,
                "question": question,
                "expected": expected,
                "actual": analysis.route,
                "reason": analysis.reason,
                "passed": expected == analysis.route,
            }
        )

    passed = sum(1 for item in results if item["passed"])
    failed = [item for item in results if not item["passed"]]

    lines = [
        "# AskData D6 语义路由评估",
        "",
        f"> 日期：2026-11-05",
        f"> 问题数：{len(results)}；通过：{passed}；失败：{len(failed)}",
        "> 规则：SQL = 生成 SQL；CLARIFY = 先追问；REFUSE = 拒答",
        "",
        "## 汇总",
        "",
        "| 指标 | 值 |",
        "|---|---:|",
        f"| 路由准确率 | {passed / len(results):.1%} |",
        f"| SQL 路由 | {sum(1 for item in results if item['actual'] == 'sql')} |",
        f"| 追问路由 | {sum(1 for item in results if item['actual'] == 'clarify')} |",
        f"| 拒答路由 | {sum(1 for item in results if item['actual'] == 'refuse')} |",
        "",
        "## 失败案例",
        "",
    ]
    if not failed:
        lines.append("无。")
    else:
        lines += [
            "| ID | 问题 | 期望 | 实际 | 原因 |",
            "|---|---|---|---|---|",
        ]
        for item in failed:
            lines.append(
                f"| {item['id']} | {item['question']} | {item['expected']} | "
                f"{item['actual']} | {item['reason']} |"
            )

    lines += ["", "## 逐题结果", "", "| ID | 问题 | 期望 | 实际 | 原因 | 结果 |", "|---|---|---|---|---|---|"]
    for item in results:
        lines.append(
            f"| {item['id']} | {item['question']} | {item['expected']} | "
            f"{item['actual']} | {item['reason']} | "
            f"{'PASS' if item['passed'] else 'FAIL'} |"
        )

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"semantic routing: {passed}/{len(results)}")
    for item in failed:
        print("FAIL", item)
    print("report:", REPORT)
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
