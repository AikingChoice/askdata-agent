"""Evaluate schema retrieval on the 40-question D0 set.

Usage:
    python scripts/eval_schema_retrieval.py
"""

from __future__ import annotations

import re
from pathlib import Path

from app.config import Settings
from app.schema_catalog import load_schema, select_tables
from app.schema_retrieval import BM25Retriever, retrieve_tables

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS = ROOT / "docs" / "questions.md"
REPORT = ROOT / "docs" / "schema_retrieval_eval.md"
KS = (3, 5, 8)


def parse_questions() -> tuple[list[tuple[str, str, list[str]]], int]:
    records = []
    skipped = 0
    for line in QUESTIONS.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| Q"):
            continue
        parts = [part.strip() for part in line.strip().strip("|").split("|")]
        if len(parts) < 6:
            skipped += 1
            continue
        qid, question, table_text = parts[0], parts[1], parts[3]
        expected = []
        if table_text and table_text != "—":
            expected = [
                table.strip().strip("`")
                for table in table_text.split(",")
                if table.strip()
            ]
        records.append((qid, question, expected))
    return records, skipped


def keyword_tables(question: str, schema: dict, k: int, retriever=None) -> list[str]:
    return select_tables(question, schema, limit=k)


def bm25_tables(question: str, schema: dict, k: int, retriever=None) -> list[str]:
    retriever = retriever or BM25Retriever(schema)
    hits = retriever.search(question, k=k)
    tables = [table for score, table in hits if score > 0]
    return tables or ["fact_orders"]


def bm25_fk_tables(question: str, schema: dict, k: int, retriever=None) -> list[str]:
    return retrieve_tables(question, schema, top_k=k, retriever=retriever)


def main() -> None:
    schema = load_schema(Settings().db_path)
    retriever = BM25Retriever(schema)
    records, skipped = parse_questions()
    with_tables = [record for record in records if record[2]]

    methods = [
        ("keyword", keyword_tables),
        ("bm25", bm25_tables),
        ("bm25_fk", bm25_fk_tables),
    ]

    summary = {}
    for name, method in methods:
        summary[name] = {}
        for k in KS:
            recalls = []
            all_hits = []
            for _, question, expected in with_tables:
                retrieved = method(question, schema, k, retriever)
                overlap = set(expected) & set(retrieved)
                recalls.append(len(overlap) / len(expected))
                all_hits.append(set(expected).issubset(set(retrieved)))
            summary[name][k] = {
                "recall": sum(recalls) / len(recalls),
                "all_hit": sum(all_hits) / len(all_hits),
            }

    lines = [
        "# AskData D4 Schema 检索评估",
        "",
        f"> 日期：2026-11-05",
        f"> 问题总数：{len(records)}（有表期望 {len(with_tables)}，对抗/无表期望跳过 {skipped}）",
        "> 方法：keyword baseline / BM25 / BM25 + 外键图",
        "",
        "## 1. 汇总",
        "",
        "| 方法 | recall@3 | all-hit@3 | recall@5 | all-hit@5 | recall@8 | all-hit@8 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name, _ in methods:
        row = [name]
        for k in KS:
            row.append(f"{summary[name][k]['recall']:.1%}")
            row.append(f"{summary[name][k]['all_hit']:.1%}")
        lines.append("| " + " | ".join(row) + " |")

    lines += ["", "## 2. BM25 + FK 的失败案例（k=8）", ""]
    failures = []
    for qid, question, expected in with_tables:
        retrieved = bm25_fk_tables(question, schema, 8, retriever)
        missing = sorted(set(expected) - set(retrieved))
        if missing:
            failures.append((qid, question, expected, retrieved, missing))
    if not failures:
        lines.append("无。")
    else:
        lines += [
            "| ID | 问题 | 期望表 | 实际召回 | 缺失 |",
            "|---|---|---|---|---|",
        ]
        for qid, question, expected, retrieved, missing in failures:
            lines.append(
                f"| {qid} | {question} | {', '.join(expected)} | "
                f"{', '.join(retrieved)} | {', '.join(missing)} |"
            )

    lines += ["", "## 3. 逐题结果（BM25 + FK, k=8）", ""]
    lines += [
        "| ID | 问题 | 期望 | 召回 | 结果 |",
        "|---|---|---|---|---|",
    ]
    for qid, question, expected in with_tables:
        retrieved = bm25_fk_tables(question, schema, 8, retriever)
        passed = set(expected).issubset(set(retrieved))
        lines.append(
            f"| {qid} | {question} | {', '.join(expected)} | "
            f"{', '.join(retrieved)} | {'PASS' if passed else 'FAIL'} |"
        )

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("== D4 schema retrieval ==")
    print(f"questions={len(records)} with_tables={len(with_tables)} skipped={skipped}")
    for name, _ in methods:
        print(name)
        for k in KS:
            metric = summary[name][k]
            print(f"  k={k} recall={metric['recall']:.1%} all_hit={metric['all_hit']:.1%}")
    print("failures(k=8):", len(failures))
    for failure in failures:
        print(" ", failure[0], "missing", failure[4])
    print("report:", REPORT)
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
