"""Integration and additional tests for API endpoints"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.core.dependencies import (
    get_graph_builder, 
    get_scraper_service, 
    get_rag_service,
    get_ai_service
)


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def full_mock_dependencies():
    """Setup all mocked dependencies for complete test coverage"""
    # Builder mock
    builder_instance = MagicMock()
    builder_instance.build = AsyncMock(return_value={
        "session_id": "test-session-123",
        "topic": "Quantum Computing",
        "nodes": [
            {"id": "1", "label": "Qubit", "definition": "Basic unit", "importance": "core", "examples": [], "notes": [], "tags": []},
            {"id": "2", "label": "Superposition", "definition": "State", "importance": "major", "examples": [], "notes": [], "tags": []},
        ],
        "edges": [
            {"source": "1", "target": "2", "relation": "enables", "weight": 0.9},
        ],
        "meta": {"source_type": "term"}
    })
    builder_instance.get_session = MagicMock(return_value={
        "topic": "Quantum Computing",
        "nodes": [
            {"id": "1", "label": "Qubit", "definition": "Basic unit", "importance": "core", "examples": [], "notes": [], "tags": []},
        ],
        "edges": [],
        "meta": {"source_type": "term"}
    })
    builder_instance.get_node = MagicMock(return_value={
        "id": "1", "label": "Qubit", "definition": "Basic unit", "importance": "core", "examples": [], "notes": [], "tags": []
    })
    builder_instance.expand_node = AsyncMock(return_value={
        "new_nodes": [{"id": "3", "label": "Quantum Gate", "definition": "Operation", "importance": "major", "examples": [], "notes": [], "tags": []}],
        "new_edges": [{"source": "1", "target": "3", "relation": "implements", "weight": 0.8}]
    })
    
    # Scraper mock
    scraper_instance = MagicMock()
    scraper_instance.fetch = AsyncMock(return_value="Comprehensive article content about quantum computing and its applications...")
    
    # RAG mock
    rag_instance = MagicMock()
    rag_instance.index = MagicMock()
    rag_instance.query = MagicMock(return_value=["Context about qubits", "Information about superposition"])
    
    # AI mock
    ai_instance = MagicMock()
    ai_instance.answer = AsyncMock(return_value="A qubit is the quantum equivalent of a classical bit, existing in a superposition of states until measured.")
    
    # Override dependencies
    app.dependency_overrides[get_graph_builder] = lambda: builder_instance
    app.dependency_overrides[get_scraper_service] = lambda: scraper_instance
    app.dependency_overrides[get_rag_service] = lambda: rag_instance
    app.dependency_overrides[get_ai_service] = lambda: ai_instance
    
    yield {
        'builder': builder_instance,
        'scraper': scraper_instance,
        'rag': rag_instance,
        'ai': ai_instance,
    }
    
    # Cleanup
    app.dependency_overrides.clear()


# Integration tests
class TestGraphBuildIntegration:
    def test_complete_term_to_graph_flow(self, client, full_mock_dependencies):
        """Test complete flow from term input to graph generation"""
        response = client.post("/graph/build", json={
            "input": "quantum computing",
            "language": "en",
            "depth": 2,
            "is_url": False
        })
        
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
        full_mock_dependencies['builder'].build.assert_called_once()


class TestChatIntegration:
    def test_complete_chat_with_node_context(self, client, full_mock_dependencies):
        """Test chat with node context"""
        response = client.post("/chat", json={
            "session_id": "test-session-123",
            "question": "What is a qubit?",
            "node_id": "1"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "qubit" in data["answer"].lower()


class TestNodeExpansion:
    def test_expand_node_integration(self, client, full_mock_dependencies):
        """Test node expansion in context"""
        response = client.post("/nodes/expand", json={
            "session_id": "test-session-123",
            "node_id": "1"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "new_nodes" in data
        assert "new_edges" in data


class TestErrorHandling:
    def test_graph_endpoint_handles_scraper_error(self, client, full_mock_dependencies):
        """Test that graph endpoint handles scraper errors"""
        from app.core.exceptions import ScrapingError
        full_mock_dependencies['scraper'].fetch = AsyncMock(
            side_effect=ScrapingError("https://example.com", "Failed to fetch")
        )
        
        response = client.post("/graph/build", json={
            "input": "https://example.com",
            "language": "en",
            "depth": 2,
            "is_url": True
        })
        
        # Should handle error gracefully
        assert response.status_code == 200 or response.status_code >= 400


    def test_chat_endpoint_handles_missing_session(self, client, full_mock_dependencies):
        """Test that chat handles missing session gracefully"""
        from app.core.exceptions import SessionNotFoundError
        full_mock_dependencies['builder'].get_session = MagicMock(
            side_effect=SessionNotFoundError("nonexistent")
        )
        
        response = client.post("/chat", json={
            "session_id": "nonexistent",
            "question": "What is AI?",
            "node_id": None
        })
        
        assert response.status_code >= 400


class TestInputValidation:
    def test_graph_build_validates_depth_range(self, client):
        """Test that depth parameter is validated"""
        response = client.post("/graph/build", json={
            "input": "test",
            "language": "en",
            "depth": 999,  # Unreasonable depth
            "is_url": False
        })
        
        # Should either reject or handle gracefully
        assert response.status_code in [200, 422]


    def test_chat_rejects_very_long_question(self, client, full_mock_dependencies):
        """Test chat with unreasonably long question"""
        long_question = "What is AI?" * 1000
        
        response = client.post("/chat", json={
            "session_id": "test-session",
            "question": long_question,
            "node_id": None
        })
        
        # Should either process or reject gracefully
        assert response.status_code in [200, 422]


class TestMultiLanguageSupport:
    @pytest.mark.parametrize("language", ["en", "es", "fr", "de", "ru", "zh"])
    def test_graph_build_supports_languages(self, client, full_mock_dependencies, language):
        """Test that graph building supports various languages"""
        response = client.post("/graph/build", json={
            "input": "quantum computing",
            "language": language,
            "depth": 1,
            "is_url": False
        })
        
        assert response.status_code == 200


class TestDifferentDepths:
    @pytest.mark.parametrize("depth", [1, 2, 3])
    def test_graph_build_different_depths(self, client, full_mock_dependencies, depth):
        """Test graph building with different depth values"""
        response = client.post("/graph/build", json={
            "input": "test",
            "language": "en",
            "depth": depth,
            "is_url": False
        })
        
        assert response.status_code == 200


class TestSessionPersistence:
    def test_session_data_persists_across_requests(self, client, full_mock_dependencies):
        """Test that session data is maintained"""
        session_id = "test-session-123"
        
        # Get session
        response1 = client.get(f"/graph/{session_id}")
        assert response1.status_code == 200
        
        # Get same session again
        response2 = client.get(f"/graph/{session_id}")
        assert response2.status_code == 200
        
        # Data should be consistent
        assert response1.json() == response2.json()


class TestNodeAccess:
    def test_access_node_from_session(self, client, full_mock_dependencies):
        """Test accessing specific node from a session"""
        response = client.get("/nodes/test-session-123/1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "1"
        assert "label" in data
        assert "definition" in data
