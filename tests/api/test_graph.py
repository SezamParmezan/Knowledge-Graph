"""Tests for /graph API endpoints"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.core.dependencies import get_graph_builder, get_scraper_service, get_rag_service
from app.schemas.graph import GraphResponse, NodeSchema, EdgeSchema


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def mock_dependencies():
    """Mock all dependencies for graph endpoints using dependency_overrides"""
    # Setup builder mock
    builder_instance = MagicMock()
    builder_instance.build = AsyncMock()
    builder_instance.get_session = MagicMock()
    
    # Setup scraper mock
    scraper_instance = MagicMock()
    scraper_instance.fetch = AsyncMock(return_value="Article content here...")
    scraper_instance.close = AsyncMock()
    
    # Setup RAG mock
    rag_instance = MagicMock()
    rag_instance.index = MagicMock()
    
    # Override dependencies
    app.dependency_overrides[get_graph_builder] = lambda: builder_instance
    app.dependency_overrides[get_scraper_service] = lambda: scraper_instance
    app.dependency_overrides[get_rag_service] = lambda: rag_instance
    
    yield {
        'builder': builder_instance,
        'scraper': scraper_instance,
        'rag': rag_instance,
    }
    
    # Clean up
    app.dependency_overrides.clear()


def test_build_graph_with_term_input(client, mock_dependencies):
    """Test building graph from term input"""
    from app.schemas.graph import GraphResponse, NodeSchema, EdgeSchema
    
    # Create proper GraphResponse object
    graph_response = GraphResponse(
        session_id="test-session",
        topic="Test Topic",
        nodes=[],
        edges=[],
        meta={"source_type": "term"}
    )
    mock_dependencies['builder'].build = AsyncMock(return_value=graph_response)
    
    # Keep original return for compatibility
    mock_dependencies['builder'].build = AsyncMock(return_value={
        "session_id": "test-session",
        "topic": "Test Topic",
        "nodes": [],
        "edges": [],
        "meta": {"source_type": "term"}
    })
    
    response = client.post("/api/graph/build", json={
        "input": "artificial intelligence",
        "language": "en",
        "depth": 2,
        "is_url": False
    })
    
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")


def test_build_graph_with_url_input(client, mock_dependencies):
    """Test building graph from URL input"""
    mock_dependencies['scraper'].fetch = AsyncMock(return_value="Article content here...")
    
    from app.schemas.graph import GraphResponse
    graph_response = GraphResponse(
        session_id="test-session",
        topic="Article Title",
        nodes=[],
        edges=[],
        meta={"source_type": "url"}
    )
    mock_dependencies['builder'].build = AsyncMock(return_value=graph_response)
    
    # Keep original for compatibility  
    mock_dependencies['builder'].build = AsyncMock(return_value={
        "session_id": "test-session",
        "topic": "Article Title",
        "nodes": [],
        "edges": [],
        "meta": {"source_type": "url"}
    })
    
    response = client.post("/api/graph/build", json={
        "input": "https://example.com/article",
        "language": "en",
        "depth": 2,
        "is_url": True
    })
    
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")


def test_get_graph_session(client, mock_dependencies):
    """Test getting existing graph session"""
    session_data = {
        "session_id": "test-session-123",
        "topic": "Test Topic",
        "nodes": [{"id": "1", "label": "Node 1"}],
        "edges": [{"source": "1", "target": "2"}],
        "meta": {"source_type": "term"}
    }
    mock_dependencies['builder'].get_session = MagicMock(return_value=session_data)
    
    response = client.get("/api/graph/test-session-123")
    
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test-session-123"
    assert data["topic"] == "Test Topic"


def test_get_graph_invalid_session(client, mock_dependencies):
    """Test getting non-existent graph session"""
    from app.core.exceptions import SessionNotFoundError
    mock_dependencies['builder'].get_session = MagicMock(
        side_effect=SessionNotFoundError("test-session")
    )
    
    response = client.get("/api/graph/invalid-session")
    
    # Should return 404 or appropriate error
    assert response.status_code >= 400


def test_build_graph_missing_required_fields(client):
    """Test that build_graph validates required fields"""
    response = client.post("/api/graph/build", json={
        "input": "test"
        # Missing language, depth, is_url
    })
    
    # Should return validation error
    assert response.status_code == 422


def test_build_graph_different_languages(client, mock_dependencies):
    """Test building graph with different languages"""
    mock_dependencies['builder'].build = AsyncMock(return_value={
        "session_id": "test-session",
        "topic": "Test",
        "nodes": [],
        "edges": [],
        "meta": {"source_type": "term"}
    })
    
    languages = ["en", "es", "fr", "de"]
    for lang in languages:
        response = client.post("/api/graph/build", json={
            "input": "test term",
            "language": lang,
            "depth": 2,
            "is_url": False
        })
        assert response.status_code == 200


def test_build_graph_different_depths(client, mock_dependencies):
    """Test building graph with different depth values"""
    mock_dependencies['builder'].build = AsyncMock(return_value={
        "session_id": "test-session",
        "topic": "Test",
        "nodes": [],
        "edges": [],
        "meta": {"source_type": "term"}
    })
    
    depths = [1, 2, 3]
    for depth in depths:
        response = client.post("/api/graph/build", json={
            "input": "test term",
            "language": "en",
            "depth": depth,
            "is_url": False
        })
        assert response.status_code == 200
