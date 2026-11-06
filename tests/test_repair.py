from app.config import Settings
from app.metrics import load_metrics
from app.pipeline import AskPipeline
from app.schema_catalog import load_schema

GOOD_SQL = (
    "SELECT ROUND(SUM(net_amount), 2) AS gmv "
    "FROM fact_orders "
    "WHERE date_id BETWEEN 20261001 AND 20261031 "
    "AND status <> 'cancelled'"
)


class FlakyLLM:
    model = "flaky"

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def generate_sql(
        self,
        question,
        schema_text,
        metrics_text,
        previous_sql=None,
        error=None,
    ):
        index = min(self.calls, len(self.responses) - 1)
        self.calls += 1
        return self.responses[index]


def make_pipeline(llm):
    settings = Settings(llm_mode="mock")
    return AskPipeline(
        settings,
        load_schema(settings.db_path),
        load_metrics(settings.metrics_path),
        llm,
    )


def test_repair_after_execution_error():
    llm = FlakyLLM(["SELECT missing_column FROM fact_orders", GOOD_SQL])
    result = make_pipeline(llm).ask("上月 GMV 是多少？")

    assert result["attempts"] == 2
    assert result["guard_ok"] is True
    assert result["error"] is None
    assert result["rows"][0]["gmv"] == 61609.57
    assert "repair" in result["trace"]


def test_repair_after_guard_error():
    llm = FlakyLLM(["DELETE FROM fact_orders", GOOD_SQL])
    result = make_pipeline(llm).ask("上月 GMV 是多少？")

    assert result["attempts"] == 2
    assert result["guard_ok"] is True
    assert result["error"] is None
    assert result["trace"].count("repair") == 1


def test_max_attempts_stops():
    llm = FlakyLLM(["SELECT missing_column FROM fact_orders"])
    result = make_pipeline(llm).ask("上月 GMV 是多少？")

    assert result["attempts"] == 3
    assert result["error"]
    assert result["trace"].count("generate") == 3
    assert result["trace"].count("repair") == 2


def test_success_trace():
    llm = FlakyLLM([GOOD_SQL])
    result = make_pipeline(llm).ask("上月 GMV 是多少？")

    assert result["attempts"] == 1
    assert result["trace"] == ["analyze", "retrieve", "generate", "guard", "execute"]
