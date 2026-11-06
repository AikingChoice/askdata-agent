from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_index_page():
    app = create_app(Settings(llm_mode="mock"))
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "AskData" in response.text
        assert "/api/ask" in response.text


def test_health():
    app = create_app(Settings(llm_mode="mock"))
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["model"] == "mock"
        assert response.json()["tables"] == 10


def test_schema():
    app = create_app(Settings(llm_mode="mock"))
    with TestClient(app) as client:
        response = client.get("/api/schema")
        assert response.status_code == 200
        assert "fact_orders" in response.json()["tables"]
        assert "dim_dates" in response.json()["tables"]


def test_ask_gmv_mock():
    app = create_app(Settings(llm_mode="mock"))
    with TestClient(app) as client:
        response = client.post(
            "/api/ask", json={"question": "上月 GMV 是多少？"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["guard_ok"] is True
        assert data["row_count"] == 1
        assert data["columns"] == ["gmv"]
        assert abs(data["rows"][0]["gmv"] - 61609.57) < 0.01
        assert "fact_orders" in data["selected_tables"]
        assert data["sql"]
        assert "LIMIT" in data["sql"].upper()
        assert data["attempts"] == 1
        assert data["route"] == "sql"
        assert data["trace"] == ["analyze", "retrieve", "generate", "guard", "execute"]


def test_clarify_recent_sales():
    app = create_app(Settings(llm_mode="mock"))
    with TestClient(app) as client:
        response = client.post(
            "/api/ask", json={"question": "最近销售怎么样？"}
        )
        data = response.json()
        assert response.status_code == 200
        assert data["route"] == "clarify"
        assert data["sql"] is None
        assert data["row_count"] == 0
        assert data["attempts"] == 0
        assert data["answer"]
        assert data["trace"] == ["analyze"]


def test_clarify_sales_caliber():
    app = create_app(Settings(llm_mode="mock"))
    with TestClient(app) as client:
        response = client.post(
            "/api/ask", json={"question": "上个月销售额是多少？"}
        )
        data = response.json()
        assert data["route"] == "clarify"
        assert data["analysis"]["reason"] == "sales_caliber"


def test_refuse_pii():
    app = create_app(Settings(llm_mode="mock"))
    with TestClient(app) as client:
        response = client.post(
            "/api/ask", json={"question": "查一下用户的身份证号"}
        )
        data = response.json()
        assert data["route"] == "refuse"
        assert data["analysis"]["reason"] == "pii"
        assert data["sql"] is None


def test_refuse_write():
    app = create_app(Settings(llm_mode="mock"))
    with TestClient(app) as client:
        response = client.post(
            "/api/ask", json={"question": "把 orders 表删了"}
        )
        data = response.json()
        assert data["route"] == "refuse"
        assert data["analysis"]["reason"] == "write_operation"
