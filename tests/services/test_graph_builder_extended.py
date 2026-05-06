"""Additional service tests for better coverage"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.graph_builder import GraphBuilder


@pytest.fixture
def mock_ai_service():
    """Mock AI service"""
    service = MagicMock()
    service.build_graph = AsyncMock()
    service.expand_node = AsyncMock()
    service.answer = AsyncMock()
    return service


@pytest.fixture
def graph_builder(mock_ai_service):
    """Create GraphBuilder with mocked AI service"""
    return GraphBuilder(mock_ai_service)


class TestGraphBuilderBuildMethod:
    @pytest.mark.asyncio
    async def test_build_creates_unique_session_ids(self, graph_builder, mock_ai_service):
        """Test that each build creates a unique session"""
        mock_ai_service.build_graph.return_value = {
            "topic": "Test",
            "nodes": [],
            "edges": []
        }
        
        result1 = await graph_builder.build("test1", "en", 1, "term")
        result2 = await graph_builder.build("test2", "en", 1, "term")
        
        assert result1.session_id != result2.session_id


    @pytest.mark.asyncio
    async def test_build_stores_session_data(self, graph_builder, mock_ai_service):
        """Test that build stores session data correctly"""
        test_graph = {
            "topic": "Test Topic",
            "nodes": [{"id": "1", "label": "Node"}],
            "edges": []
        }
        mock_ai_service.build_graph.return_value = test_graph
        
        result = await graph_builder.build("test", "en", 1, "term")
        
        stored_session = graph_builder.get_session(result.session_id)
        assert stored_session == test_graph


    @pytest.mark.asyncio
    async def test_build_calls_ai_with_correct_params(self, graph_builder, mock_ai_service):
        """Test that build calls AI service with correct parameters"""
        mock_ai_service.build_graph.return_value = {"topic": "Test", "nodes": [], "edges": []}
        
        await graph_builder.build("test input", "ru", 3, "url")
        
        mock_ai_service.build_graph.assert_called_once_with(
            "test input", "ru", 3, "url"
        )


class TestGraphBuilderGetNode:
    def test_get_node_from_existing_session(self, graph_builder):
        """Test retrieving node from existing session"""
        test_graph = {
            "topic": "Test",
            "nodes": [
                {"id": "node1", "label": "Node 1", "definition": "Def 1"},
                {"id": "node2", "label": "Node 2", "definition": "Def 2"}
            ],
            "edges": []
        }
        
        graph_builder.sessions["session1"] = test_graph
        
        node = graph_builder.get_node("session1", "node1")
        assert node["label"] == "Node 1"


    def test_get_node_raises_for_missing_node(self, graph_builder):
        """Test that getting missing node raises error"""
        from app.core.exceptions import NodeNotFoundError
        
        test_graph = {
            "topic": "Test",
            "nodes": [{"id": "node1", "label": "Node 1"}],
            "edges": []
        }
        
        graph_builder.sessions["session1"] = test_graph
        
        with pytest.raises(NodeNotFoundError):
            graph_builder.get_node("session1", "nonexistent")


class TestGraphBuilderExpandNode:
    @pytest.mark.asyncio
    async def test_expand_node_adds_new_nodes(self, graph_builder, mock_ai_service):
        """Test that expand_node adds new nodes to graph"""
        initial_graph = {
            "topic": "Test",
            "nodes": [{"id": "1", "label": "Node 1"}],
            "edges": []
        }
        
        graph_builder.sessions["session1"] = initial_graph
        
        mock_ai_service.expand_node.return_value = {
            "new_nodes": [{"id": "2", "label": "Node 2"}],
            "new_edges": [{"source": "1", "target": "2"}]
        }
        
        await graph_builder.expand_node("session1", "1")
        
        # Verify new nodes were added
        updated_graph = graph_builder.sessions["session1"]
        assert len(updated_graph["nodes"]) == 2


class TestBuildNodesAndEdges:
    def test_build_nodes_converts_correctly(self, graph_builder):
        """Test node schema conversion"""
        graph = {
            "nodes": [
                {
                    "id": "1",
                    "label": "Test",
                    "definition": "Def",
                    "importance": "core",
                    "examples": ["ex1"],
                    "notes": ["note1"],
                    "tags": ["tag1"]
                }
            ]
        }
        
        nodes = graph_builder._build_nodes(graph)
        
        assert len(nodes) == 1
        assert nodes[0].id == "1"
        assert nodes[0].label == "Test"


    def test_build_edges_converts_correctly(self, graph_builder):
        """Test edge schema conversion"""
        graph = {
            "edges": [
                {
                    "source": "1",
                    "target": "2",
                    "relation": "connected",
                    "weight": 0.8
                }
            ]
        }
        
        edges = graph_builder._build_edges(graph)
        
        assert len(edges) == 1
        assert edges[0].source == "1"
        assert edges[0].target == "2"
        assert edges[0].weight == 0.8
