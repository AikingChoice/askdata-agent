from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"


def _path(name: str, default: Path) -> Path:
    return Path(os.getenv(name, str(default))).resolve()


@dataclass
class Settings:
    db_path: Path = field(
        default_factory=lambda: _path("ASK_DATA_DB", DATA_DIR / "askdata.db")
    )
    metrics_path: Path = field(default_factory=lambda: DATA_DIR / "metrics.yml")
    llm_mode: str = field(default_factory=lambda: os.getenv("LLM_MODE", "deepseek"))
    deepseek_api_key: str = field(default_factory=lambda: os.getenv("DEEPSEEK_API_KEY", ""))
    deepseek_base_url: str = field(
        default_factory=lambda: os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    )
    deepseek_model: str = field(
        default_factory=lambda: os.getenv("DEEPSEEK_MODEL", "deepseek-flash")
    )
    timeout_seconds: float = field(
        default_factory=lambda: float(os.getenv("ASK_TIMEOUT_SECONDS", "30"))
    )
    retrieval_top_k: int = field(
        default_factory=lambda: int(os.getenv("RETRIEVAL_TOP_K", "8"))
    )
    repair_max_attempts: int = field(
        default_factory=lambda: int(os.getenv("REPAIR_MAX_ATTEMPTS", "3"))
    )
