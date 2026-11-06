from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import Settings
from .llm import build_llm
from .metrics import load_metrics
from .observability import log_trace
from .pipeline import AskPipeline
from .schema_catalog import load_schema
from .schemas import AskRequest, AskResponse

STATIC_DIR = Path(__file__).resolve().parent / "static"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    schema = load_schema(settings.db_path)
    metrics = load_metrics(settings.metrics_path)
    llm = build_llm(settings)
    pipeline = AskPipeline(settings, schema, metrics, llm)

    app = FastAPI(
        title="AskData",
        description="可审计的 Text-to-SQL 数据问数 Agent（D3 最小闭环）",
        version="0.1.0",
    )
    app.state.settings = settings
    app.state.schema = schema
    app.state.metrics = metrics
    app.state.pipeline = pipeline

    @app.get("/api/health")
    def health() -> dict:
        return {
            "status": "ok",
            "model": getattr(llm, "model", "unknown"),
            "db": str(settings.db_path),
            "tables": len(schema),
        }

    @app.get("/api/schema")
    def schema_view() -> dict:
        return {"tables": sorted(schema.keys()), "schema": schema}

    @app.post("/api/ask", response_model=AskResponse)
    def ask(payload: AskRequest) -> AskResponse:
        result = pipeline.ask(payload.question)
        log_trace(payload.question, result)
        return AskResponse(**result)

    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
    return app


app = create_app()
