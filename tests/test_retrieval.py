from app.config import Settings
from app.schema_catalog import load_schema
from app.schema_retrieval import BM25Retriever, build_fk_graph, retrieve_tables


def get_schema():
    return load_schema(Settings().db_path)


def test_bm25_finds_gmv_tables():
    schema = get_schema()
    selected = retrieve_tables("上月 GMV 是多少？", schema, top_k=6)
    assert "fact_orders" in selected
    assert "dim_dates" in selected


def test_bm25_finds_category_tables():
    schema = get_schema()
    selected = retrieve_tables("本月各品类销售额 top 3", schema, top_k=6)
    assert "fact_orders" in selected
    assert "fact_order_items" in selected
    assert "dim_products" in selected
    assert "dim_dates" in selected


def test_fk_graph_expands_to_refunds():
    schema = get_schema()
    graph = build_fk_graph(schema)
    assert "fact_refunds" in graph["fact_orders"]
    assert "fact_orders" in graph["fact_refunds"]

    selected = retrieve_tables("连续 3 个月毛利率下降的品类", schema, top_k=8)
    assert "fact_refunds" in selected


def test_bm25_returns_seed_tables():
    schema = get_schema()
    hits = BM25Retriever(schema).search("各区域退款率", k=5)
    tables = [table for score, table in hits]
    assert "fact_refunds" in tables
    assert "dim_regions" in tables


def test_empty_query_falls_back():
    schema = get_schema()
    selected = retrieve_tables("随便问问", schema, top_k=6)
    assert selected
