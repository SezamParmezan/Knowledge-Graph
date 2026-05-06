"""Tests for main.py routes"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def mock_scraper():
    """Mock the scraper service to avoid async cleanup issues"""
    with patch('app.main.get_scraper_service') as mock:
        mock_instance = MagicMock()
        mock_instance.close = MagicMock()
        mock.return_value = mock_instance
        yield mock


def test_selection_page_returns_200(client):
    """Test that selection page returns 200 status code"""
    response = client.get("/")
    assert response.status_code == 200


def test_selection_page_returns_html(client):
    """Test that selection page returns HTML content"""
    response = client.get("/")
    assert "text/html" in response.headers.get("content-type", "")


def test_graph_page_returns_200(client):
    """Test that graph page returns 200 status code"""
    response = client.get("/graph/test-session-123")
    assert response.status_code == 200


def test_graph_page_with_different_session_ids(client):
    """Test graph page with various session IDs"""
    session_ids = ["session-1", "uuid-12345", "test_session"]
    for session_id in session_ids:
        response = client.get(f"/graph/{session_id}")
        assert response.status_code == 200


def test_static_files_mounted(client):
    """Test that static files are properly mounted"""
    # Just verify the static mount doesn't crash the app
    response = client.get("/")
    assert response.status_code == 200


def test_api_routers_included(client):
    """Test that API routers are included and accessible"""
    # Test graph endpoint exists
    response = client.post("/graph/build", json={
        "input": "test",
        "language": "en",
        "depth": 2,
        "is_url": False
    })
    # Should not return 404 (endpoint exists, but may fail for other reasons)
    assert response.status_code != 404


def test_exception_handlers_registered():
    """Test that exception handlers are properly registered"""
    # Verify that exception handlers are in the app
    assert len(app.exception_handlers) > 0
