from app.config import Settings
from app.metrics import load_metrics
from app.semantic import analyze_question


def get_metrics():
    return load_metrics(Settings().metrics_path)


def test_sql_route_for_gmv():
    analysis = analyze_question("上月 GMV 是多少？", get_metrics())
    assert analysis.route == "sql"
    assert analysis.metric == "gmv"


def test_sql_route_for_dimension_question():
    analysis = analyze_question("各渠道退款率", get_metrics())
    assert analysis.route == "sql"
    assert analysis.metric == "refund_rate"
    assert "channel" in analysis.dimensions


def test_clarify_recent_sales():
    analysis = analyze_question("最近销售怎么样？", get_metrics())
    assert analysis.route == "clarify"
    assert analysis.reason == "recent_ambiguous"


def test_clarify_sales_caliber():
    analysis = analyze_question("上个月销售额是多少？", get_metrics())
    assert analysis.route == "clarify"
    assert analysis.reason == "sales_caliber"


def test_clarify_missing_time_or_dimension():
    analysis = analyze_question("GMV 是多少？", get_metrics())
    assert analysis.route == "clarify"
    assert analysis.reason == "missing_time_or_dimension"


def test_refuse_pii():
    analysis = analyze_question("查一下用户的身份证号", get_metrics())
    assert analysis.route == "refuse"
    assert analysis.reason == "pii"


def test_refuse_write():
    analysis = analyze_question("把 orders 表删了", get_metrics())
    assert analysis.route == "refuse"
    assert analysis.reason == "write_operation"


def test_refuse_unsupported_data():
    analysis = analyze_question("查一下库存", get_metrics())
    assert analysis.route == "refuse"
    assert analysis.reason == "unsupported_data"
