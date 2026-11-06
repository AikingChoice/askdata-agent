"""D3 smoke test: real DeepSeek -> guard -> read-only execution."""

from __future__ import annotations

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


def main() -> None:
    question = sys.argv[1] if len(sys.argv) > 1 else "上月 GMV 是多少？"
    settings = Settings()
    pipeline = AskPipeline(
        settings,
        load_schema(settings.db_path),
        load_metrics(settings.metrics_path),
        build_llm(settings),
    )
    result = pipeline.ask(question)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
