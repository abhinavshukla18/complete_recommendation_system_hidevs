"""Tests for the Flask API."""
import pytest

from api.app import create_app
from engine.orchestrator import RecommendationOrchestrator


@pytest.fixture
def client(session):
    """A test client that uses the in-memory seeded database."""
    orchestrator = RecommendationOrchestrator(session)
    app = create_app(orchestrator=orchestrator)
    return app.test_client()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_recommend_returns_results(client):
    response = client.get("/recommend/1?limit=3")
    assert response.status_code == 200
    data = response.get_json()
    assert data["user_id"] == 1
    assert data["count"] == len(data["recommendations"])
    assert 0 < data["count"] <= 3


def test_recommend_unknown_user_gives_404(client):
    response = client.get("/recommend/9999")
    assert response.status_code == 404
    assert "error" in response.get_json()


def test_recommend_bad_user_id_gives_400(client):
    response = client.get("/recommend/abc")
    assert response.status_code == 400


def test_recommend_bad_limit_gives_400(client):
    response = client.get("/recommend/1?limit=0")
    assert response.status_code == 400


def test_feedback_is_recorded(client):
    response = client.post("/feedback", json={
        "user_id": 1, "content_id": 1, "type": "like", "rating": 5})
    assert response.status_code == 201
    assert response.get_json()["status"] == "recorded"


def test_feedback_unknown_user_gives_404(client):
    response = client.post("/feedback", json={
        "user_id": 9999, "content_id": 1, "type": "like", "rating": 5})
    assert response.status_code == 404


def test_feedback_unknown_content_gives_404(client):
    response = client.post("/feedback", json={
        "user_id": 1, "content_id": 9999, "type": "like", "rating": 5})
    assert response.status_code == 404


def test_feedback_missing_type_gives_400(client):
    response = client.post("/feedback", json={
        "user_id": 1, "content_id": 1})
    assert response.status_code == 400


def test_feedback_not_json_gives_400(client):
    response = client.post("/feedback", data="hello")
    assert response.status_code == 400


def test_metrics_counts_requests(client):
    client.get("/health")
    client.get("/recommend/1")
    data = client.get("/metrics").get_json()
    assert data["requests"] >= 2
    assert "average_response_ms" in data
    assert "cache" in data


def test_api_key_required(session):
    orchestrator = RecommendationOrchestrator(session)
    app = create_app(orchestrator=orchestrator, api_key="secret")
    client = app.test_client()

    assert client.get("/health").status_code == 200
    assert client.get("/recommend/1").status_code == 401
    ok = client.get("/recommend/1", headers={"X-API-Key": "secret"})
    assert ok.status_code == 200
