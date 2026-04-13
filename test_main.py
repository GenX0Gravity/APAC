"""
Tests for the Text Summarizer Agent API.
Run with: pytest tests/ -v
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

# Import app after patching ADK so we don't need real credentials in CI
with patch("google.adk.agents.Agent"), patch("google.adk.runners.Runner"):
    from main import app

client = TestClient(app)


def test_health_check():
    """GET /health should return 200 with status=healthy."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "agent" in data
    assert "model" in data


def test_root_endpoint():
    """GET / should list available endpoints."""
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert "endpoints" in body
    assert "POST /summarize" in body["endpoints"]


def test_summarize_missing_body():
    """POST /summarize with no body should return 422."""
    response = client.post("/summarize", json={})
    assert response.status_code == 422


def test_summarize_text_too_short():
    """POST /summarize with text under 10 chars should return 422."""
    response = client.post("/summarize", json={"text": "short"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_summarize_success():
    """POST /summarize with valid text should return 200 + summary."""
    mock_summary = "This is a mocked summary of the provided text."

    with patch("main.run_agent", new_callable=AsyncMock, return_value=mock_summary):
        response = client.post(
            "/summarize",
            json={
                "text": "The quick brown fox jumps over the lazy dog. " * 5,
                "session_id": "test-session",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["summary"] == mock_summary
    assert data["session_id"] == "test-session"
