from app.sql_guard import guard_sql

ALLOWED = {"fact_orders", "dim_dates", "fact_refunds"}


def test_valid_select_adds_limit():
    result = guard_sql("SELECT SUM(net_amount) AS gmv FROM fact_orders", ALLOWED)
    assert result.ok
    assert result.sql
    assert "LIMIT 1000" in result.sql.upper()
    assert result.tables == ["fact_orders"]


def test_existing_smaller_limit_is_preserved():
    result = guard_sql("SELECT order_id FROM fact_orders LIMIT 3", ALLOWED)
    assert result.ok
    assert "LIMIT 3" in result.sql.upper()


def test_large_limit_is_capped():
    result = guard_sql("SELECT order_id FROM fact_orders LIMIT 5000", ALLOWED)
    assert result.ok
    assert "LIMIT 1000" in result.sql.upper()


def test_reject_delete():
    result = guard_sql("DELETE FROM fact_orders", ALLOWED)
    assert not result.ok


def test_reject_multiple_statements():
    result = guard_sql(
        "SELECT * FROM fact_orders; DROP TABLE fact_orders", ALLOWED
    )
    assert not result.ok


def test_reject_unknown_table():
    result = guard_sql("SELECT * FROM salary_table", ALLOWED)
    assert not result.ok


def test_reject_qualified_table():
    result = guard_sql("SELECT * FROM main.fact_orders", ALLOWED)
    assert not result.ok


def test_cte_is_allowed():
    result = guard_sql(
        "WITH x AS (SELECT order_id FROM fact_orders) SELECT * FROM x",
        ALLOWED,
    )
    assert result.ok


def test_reject_dangerous_comment_payload():
    result = guard_sql(
        "SELECT * FROM fact_orders /* ; DROP TABLE fact_orders */",
        ALLOWED,
    )
    assert not result.ok
    assert "comment" in result.reason.lower()
