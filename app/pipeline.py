from __future__ import annotations

import time
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from .config import Settings
from .executor import execute_readonly
from .metrics import format_metrics
from .schema_catalog import format_schema
from .schema_retrieval import retrieve_tables
from .semantic import analyze_question
from .sql_guard import guard_sql


class AskState(TypedDict, total=False):
    question: str
    route: str
    answer: str
    analysis: dict
    selected_tables: list[str]
    schema_text: str
    metrics_text: str
    raw_sql: str
    sql: str | None
    guard_ok: bool
    guard_reason: str
    columns: list[str]
    rows: list[dict]
    row_count: int
    truncated: bool
    error: str | None
    last_error: str
    attempts: int
    max_attempts: int
    trace: list[str]


class AskPipeline:
    def __init__(self, settings: Settings, schema: dict, metrics: dict, llm):
        self.settings = settings
        self.schema = schema
        self.metrics = metrics
        self.llm = llm
        self.graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(AskState)
        graph.add_node("analyze", self._analyze)
        graph.add_node("retrieve", self._retrieve)
        graph.add_node("generate", self._generate)
        graph.add_node("guard", self._guard)
        graph.add_node("execute", self._execute)
        graph.add_node("repair", self._repair)

        graph.add_edge(START, "analyze")
        graph.add_conditional_edges(
            "analyze",
            self._after_analyze,
            {"retrieve": "retrieve", END: END},
        )
        graph.add_edge("retrieve", "generate")
        graph.add_edge("generate", "guard")
        graph.add_conditional_edges(
            "guard",
            self._after_guard,
            {"execute": "execute", "repair": "repair", END: END},
        )
        graph.add_conditional_edges(
            "execute",
            self._after_execute,
            {"repair": "repair", END: END},
        )
        graph.add_edge("repair", "generate")
        return graph.compile()

    @staticmethod
    def _trace(state: AskState, name: str) -> list[str]:
        return state.get("trace", []) + [name]

    def _analyze(self, state: AskState) -> dict:
        analysis = analyze_question(state["question"], self.metrics)
        return {
            "route": analysis.route,
            "answer": analysis.answer,
            "analysis": analysis.as_dict(),
            "trace": self._trace(state, "analyze"),
        }

    def _after_analyze(self, state: AskState) -> str:
        return "retrieve" if state.get("route") == "sql" else END

    def _retrieve(self, state: AskState) -> dict:
        question = state["question"]
        selected = retrieve_tables(
            question,
            self.schema,
            top_k=self.settings.retrieval_top_k,
        )
        return {
            "selected_tables": selected,
            "schema_text": format_schema(self.schema, selected),
            "metrics_text": format_metrics(self.metrics),
            "trace": self._trace(state, "retrieve"),
        }

    def _generate(self, state: AskState) -> dict:
        attempts = state.get("attempts", 0) + 1
        previous_sql = state.get("raw_sql") or None
        error = state.get("last_error") or None
        try:
            raw_sql = self.llm.generate_sql(
                state["question"],
                state["schema_text"],
                state["metrics_text"],
                previous_sql=previous_sql,
                error=error,
            )
        except Exception as exc:
            message = f"LLM error: {exc}"
            return {
                "attempts": attempts,
                "raw_sql": "",
                "last_error": message,
                "error": message,
                "trace": self._trace(state, "generate"),
            }
        return {
            "attempts": attempts,
            "raw_sql": raw_sql,
            "trace": self._trace(state, "generate"),
        }

    def _guard(self, state: AskState) -> dict:
        raw_sql = state.get("raw_sql", "")
        if not raw_sql and state.get("error"):
            reason = state["error"]
            return {
                "guard_ok": False,
                "guard_reason": reason,
                "sql": None,
                "last_error": reason,
                "trace": self._trace(state, "guard"),
            }

        result = guard_sql(raw_sql, set(self.schema.keys()))
        if not result.ok:
            return {
                "guard_ok": False,
                "guard_reason": result.reason,
                "sql": None,
                "last_error": result.reason,
                "trace": self._trace(state, "guard"),
            }
        return {
            "guard_ok": True,
            "guard_reason": result.reason,
            "sql": result.sql,
            "last_error": "",
            "error": None,
            "trace": self._trace(state, "guard"),
        }

    def _execute(self, state: AskState) -> dict:
        execution = execute_readonly(
            self.settings.db_path,
            state.get("sql") or "",
            max_rows=200,
            timeout_ms=int(self.settings.timeout_seconds * 1000),
        )
        return {
            "columns": execution.columns,
            "rows": execution.rows,
            "row_count": len(execution.rows),
            "truncated": execution.truncated,
            "error": execution.error,
            "last_error": execution.error or "",
            "trace": self._trace(state, "execute"),
        }

    def _repair(self, state: AskState) -> dict:
        return {"trace": self._trace(state, "repair")}

    def _after_guard(self, state: AskState) -> str:
        if state.get("guard_ok"):
            return "execute"
        if state.get("attempts", 0) < state.get("max_attempts", 3):
            return "repair"
        return END

    def _after_execute(self, state: AskState) -> str:
        if not state.get("error"):
            return END
        if state.get("attempts", 0) < state.get("max_attempts", 3):
            return "repair"
        return END

    def ask(self, question: str) -> dict:
        started = time.perf_counter()
        result = self.graph.invoke(
            {
                "question": question,
                "route": "",
                "answer": "",
                "analysis": {},
                "selected_tables": [],
                "schema_text": "",
                "metrics_text": "",
                "raw_sql": "",
                "sql": None,
                "guard_ok": False,
                "guard_reason": "",
                "columns": [],
                "rows": [],
                "row_count": 0,
                "truncated": False,
                "error": None,
                "last_error": "",
                "attempts": 0,
                "max_attempts": self.settings.repair_max_attempts,
                "trace": [],
            }
        )
        error = result.get("error")
        route = result.get("route", "sql")
        if route != "sql":
            error = None
        elif not error and not result.get("guard_ok"):
            error = result.get("last_error") or "query failed"
        rows = result.get("rows", [])
        return {
            "question": question,
            "route": route,
            "answer": result.get("answer", ""),
            "analysis": result.get("analysis", {}),
            "selected_tables": result.get("selected_tables", []),
            "raw_sql": result.get("raw_sql", ""),
            "sql": result.get("sql"),
            "guard_ok": bool(result.get("guard_ok", False)),
            "guard_reason": result.get("guard_reason", ""),
            "columns": result.get("columns", []),
            "rows": rows,
            "row_count": len(rows),
            "truncated": bool(result.get("truncated", False)),
            "latency_ms": int((time.perf_counter() - started) * 1000),
            "model": getattr(self.llm, "model", "unknown"),
            "attempts": result.get("attempts", 0),
            "trace": result.get("trace", []),
            "error": error,
        }
