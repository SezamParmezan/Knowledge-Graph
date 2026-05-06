"""Tests for /chat API endpoint"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.core.dependencies import get_graph_builder, get_rag_service, get_ai_service


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def mock_dependencies():
    """Mock all dependencies for chat endpoint using dependency_overrides"""
    # Setup builder mock
    builder_instance = MagicMock()
    builder_instance.get_session = MagicMock(return_value={
        "topic": "Test Topic",
        "nodes": [{"id": "1", "label": "Node 1"}],
    })
    builder_instance.get_node = MagicMock(return_value={
        "id": "1",
        "label": "Node 1",
        "definition": "Test definition"
    })
    
    # Setup RAG mock
    rag_instance = MagicMock()
    rag_instance.query = MagicMock(return_value=["Relevant context 1", "Relevant context 2"])
    
    # Setup AI mock
    ai_instance = MagicMock()
    ai_instance.answer = AsyncMock(return_value="This is the AI answer to your question.")
    
    # Override dependencies
    app.dependency_overrides[get_graph_builder] = lambda: builder_instance
    app.dependency_overrides[get_rag_service] = lambda: rag_instance
    app.dependency_overrides[get_ai_service] = lambda: ai_instance
    
    yield {
        'builder': builder_instance,
        'rag': rag_instance,
        'ai': ai_instance,
    }
    
    # Clean up
    app.dependency_overrides.clear()


def test_chat_with_session_only(client, mock_dependencies):
    """Test chat endpoint with only session_id"""
    response = client.post("/chat", json={
        "session_id": "test-session",
        "question": "What is AI?",
        "node_id": None
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert data["answer"] == "This is the AI answer to your question."


def test_chat_with_session_and_node(client, mock_dependencies):
    """Test chat endpoint with session_id and node_id"""
    response = client.post("/chat", json={
        "session_id": "test-session",
        "question": "Tell me more about this node?",
        "node_id": "node-1"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data


def test_chat_uses_rag_context(client, mock_dependencies):
    """Test that chat endpoint uses RAG context"""
    response = client.post("/chat", json={
        "session_id": "test-session",
        "question": "What is the definition?",
        "node_id": None
    })
    
    # Verify RAG query was called
    mock_dependencies['rag'].query.assert_called()
    assert response.status_code == 200


def test_chat_uses_ai_service(client, mock_dependencies):
    """Test that chat endpoint uses AI service"""
    response = client.post("/chat", json={
        "session_id": "test-session",
        "question": "Explain this concept",
        "node_id": None
    })
    
    # Verify AI answer was called
    mock_dependencies['ai'].answer.assert_called()
    assert response.status_code == 200


def test_chat_missing_session_id(client):
    """Test chat endpoint with missing session_id"""
    response = client.post("/chat", json={
        "question": "What is AI?"
    })
    
    # Should return validation error
    assert response.status_code == 422


def test_chat_missing_question(client):
    """Test chat endpoint with missing question"""
    response = client.post("/chat", json={
        "session_id": "test-session"
    })
    
    # Should return validation error
    assert response.status_code == 422


def test_chat_empty_question(client, mock_dependencies):
    """Test chat with empty question string"""
    response = client.post("/chat", json={
        "session_id": "test-session",
        "question": "",
        "node_id": None
    })
    
    # Should still process but may be handled by AI service
    # Check if validation fails or passes through
    assert response.status_code in [200, 422]


def test_chat_invalid_session_id(client, mock_dependencies):
    """Test chat with invalid session"""
    from app.core.exceptions import SessionNotFoundError
    mock_dependencies['builder'].get_session = MagicMock(
        side_effect=SessionNotFoundError("invalid-session")
    )
    
    response = client.post("/chat", json={
        "session_id": "invalid-session",
        "question": "What is AI?",
        "node_id": None
    })
    
    # Should return error
    assert response.status_code >= 400


def test_chat_with_invalid_node_id(client, mock_dependencies):
    """Test chat with invalid node_id"""
    from app.core.exceptions import NodeNotFoundError
    mock_dependencies['builder'].get_node = MagicMock(
        side_effect=NodeNotFoundError("invalid-node")
    )
    
    response = client.post("/chat", json={
        "session_id": "test-session",
        "question": "What is this?",
        "node_id": "invalid-node"
    })
    
    # Should return error
    assert response.status_code >= 400


def test_chat_response_model(client, mock_dependencies):
    """Test that chat response matches ChatResponse schema"""
    response = client.post("/chat", json={
        "session_id": "test-session",
        "question": "Test question?",
        "node_id": None
    })
    
    assert response.status_code == 200
    data = response.json()
    # ChatResponse should have 'answer' field
    assert isinstance(data, dict)
    assert "answer" in data
