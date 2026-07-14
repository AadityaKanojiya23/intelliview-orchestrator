from fastapi.testclient import TestClient
from orchestrator.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert "status" in data
    assert "timestamp" in data

def test_start_interview_invalid_candidate_id():
    response = client.post(
        "/start-interview",
        
        headers={"X-API-Token": "dev-token-change-me"},
        json={
            "candidate_id": "@@@###",
            "priority": "medium"
        },
    )

    assert response.status_code == 422

def test_session_status_not_found():
    response = client.get("/session-status/fake-session-id")

    assert response.status_code == 404
    assert response.json()["detail"] == "Session not found"    

def test_sync_to_database_without_token():
    response = client.post("/sync-to-database")

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid or missing API token"

def test_sync_to_database_with_token():
    response = client.post(
        "/sync-to-database",
        headers={"X-API-Token": "dev-token-change-me"},
    )

    assert response.status_code == 200




def test_start_interview_valid():
    response = client.post(
        "/start-interview",
        headers={"X-API-Token": "dev-token-change-me"},
        json={
            "candidate_id": "candidate-123",
            "priority": "medium",
        },
    )


    assert response.status_code == 200