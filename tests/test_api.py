from fastapi.testclient import TestClient

from app.main import app


def test_health_and_conference_list() -> None:
    with TestClient(app) as client:
        index = client.get("/")
        assert index.status_code == 200
        assert "TopConf Paper Hub" in index.text

        health = client.get("/health")
        assert health.status_code == 200

        response = client.get("/api/v1/conferences?domain=ai")
        assert response.status_code == 200
        payload = response.json()
        assert any(item["acronym"] == "NeurIPS" for item in payload)


def test_crawl_preview_api() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/crawl/preview",
            json={"conferences": ["SIGCOMM"], "years": [2025], "sources": ["dblp"]},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["total"] == 1
        assert payload["items"][0]["conference"] == "SIGCOMM"
