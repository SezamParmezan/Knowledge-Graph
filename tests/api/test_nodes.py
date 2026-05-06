"""Tests for /nodes API endpoints"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.core.dependencies import get_graph_builder


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def mock_dependencies():
    """Mock dependencies for nodes endpoints using dependency_overrides"""
    # Setup builder mock
    builder_instance = MagicMock()
    builder_instance.get_node = MagicMock(return_value={
        "id": "node-1",
        "label": "Test Node",
        "definition": "This is a test node definition"
    })
    builder_instance.expand_node = AsyncMock(return_value={
        "id": "node-1",
        "label": "Test Node",
        "definition": "This is a test node definition",
        "expanded_content": "Expanded information about the node"
    })
    
    # Override dependencies
    app.dependency_overrides[get_graph_builder] = lambda: builder_instance
    
    yield {
        'builder': builder_instance,
    }
    
    # Clean up
    app.dependency_overrides.clear()


def test_get_node_info(client, mock_dependencies):
    """Test getting node information"""
    from app.schemas.nodes import NodeDetailResponse
    
    # Setup proper response
    node_response = NodeDetailResponse(
        id="node-1",
        label="Test Node",
        definition="This is a test node definition",
        importance="core",
        examples=[],
        notes=[],
        tags=[]
    )
    mock_dependencies['builder'].get_node = MagicMock(return_value=node_response.model_dump())
    
    response = client.get("/nodes/test-session/node-1")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "node-1"
    assert data["label"] == "Test Node"
    assert "definition" in data


def test_get_node_info_different_ids(client, mock_dependencies):
    """Test getting different node infos"""
    node_ids = ["node-1", "node-abc123", "concept-xyz"]
    session_id = "test-session"
    
    for node_id in node_ids:
        response = client.get(f"/nodes/{session_id}/{node_id}")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data


def test_expand_node(client, mock_dependencies):
    """Test expanding a node"""
    response = client.post("/nodes/expand", json={
        "session_id": "test-session",
        "node_id": "node-1"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "node-1"
    assert "expanded_content" in data


def test_get_node_invalid_session(client, mock_dependencies):
    """Test getting node from invalid session"""
    from app.core.exceptions import SessionNotFoundError
    mock_dependencies['builder'].get_node = MagicMock(
        side_effect=SessionNotFoundError("invalid-session")
    )
    
    response = client.get("/nodes/invalid-session/node-1")
    
    assert response.status_code >= 400


def test_get_node_invalid_node_id(client, mock_dependencies):
    """Test getting invalid node"""
    from app.core.exceptions import NodeNotFoundError
    mock_dependencies['builder'].get_node = MagicMock(
        side_effect=NodeNotFoundError("invalid-node")
    )
    
    response = client.get("/nodes/test-session/invalid-node")
    
    assert response.status_code >= 400


def test_expand_node_missing_session_id(client):
    """Test expand endpoint with missing session_id"""
    response = client.post("/nodes/expand", json={
        "node_id": "node-1"
    })
    
    # Should return validation error
    assert response.status_code == 422


def test_expand_node_missing_node_id(client):
    """Test expand endpoint with missing node_id"""
    response = client.post("/nodes/expand", json={
        "session_id": "test-session"
    })
    
    # Should return validation error
    assert response.status_code == 422


def test_expand_node_invalid_session(client, mock_dependencies):
    """Test expanding node from invalid session"""
    from app.core.exceptions import SessionNotFoundError
    mock_dependencies['builder'].expand_node = AsyncMock(
        side_effect=SessionNotFoundError("invalid-session")
    )
    
    response = client.post("/nodes/expand", json={
        "session_id": "invalid-session",
        "node_id": "node-1"
    })
    
    assert response.status_code >= 400


def test_expand_node_invalid_node(client, mock_dependencies):
    """Test expanding invalid node"""
    from app.core.exceptions import NodeNotFoundError
    mock_dependencies['builder'].expand_node = AsyncMock(
        side_effect=NodeNotFoundError("invalid-node")
    )
    
    response = client.post("/nodes/expand", json={
        "session_id": "test-session",
        "node_id": "invalid-node"
    })
    
    assert response.status_code >= 400


def test_get_node_returns_correct_fields(client, mock_dependencies):
    """Test that node response has expected fields"""
    response = client.get("/nodes/test-session/node-1")
    
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "label" in data
    assert "definition" in data


def test_expand_node_called_with_correct_params(client, mock_dependencies):
    """Test that expand_node is called with correct parameters"""
    response = client.post("/nodes/expand", json={
        "session_id": "test-session",
        "node_id": "node-1"
    })
    
    assert response.status_code == 200
    # Verify the mock was called with correct params
    mock_dependencies['builder'].expand_node.assert_called_once()
    call_args = mock_dependencies['builder'].expand_node.call_args
    assert call_args[1]["session_id"] == "test-session"
    assert call_args[1]["node_id"] == "node-1"
