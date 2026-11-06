"""Run 5 demo questions through the AskData pipeline.

Usage:
    python scripts/demo.py
    python scripts/demo.py --mock
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import Settings  # noqa: E402
from app.llm import build_llm  # noqa: E402
from app.metrics import load_metrics  # noqa: E402
from app.pipeline import AskPipeline  # noqa: E402
from app.schema_catalog import load_schema  # noqa: E402

QUESTIONS = [
    "上月 GMV 是多少？",
    "本月各品类销售额 top 3",
    "各渠道退款率",
    "最近销售怎么样？",
    "查一下用户的身份证号",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mock", action="store_true", help="use mock LLM")
    args = parser.parse_args()

    settings = Settings(llm_mode="mock" if args.mock else "deepseek")
    pipeline = AskPipeline(
        settings,
        load_schema(settings.db_path),
        load_metrics(settings.metrics_path),
        build_llm(settings),
    )

    for question in QUESTIONS:
        result = pipeline.ask(question)
        print("=" * 78)
        print("Q:", question)
        print("route:", result["route"])
        if result["route"] != "sql":
            print("answer:", result["answer"])
            print("analysis:", json.dumps(result["analysis"], ensure_ascii=False))
            continue
        print("sql:", result["sql"])
        print("rows:", json.dumps(result["rows"][:5], ensure_ascii=False))
        print(
            "meta:",
            json.dumps(
                {
                    "row_count": result["row_count"],
                    "attempts": result["attempts"],
                    "latency_ms": result["latency_ms"],
                    "trace": result["trace"],
                    "error": result["error"],
                },
                ensure_ascii=False,
            ),
        )


if __name__ == "__main__":
    main()
