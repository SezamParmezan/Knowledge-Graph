import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.graph_builder import GraphBuilder
from app.schemas.graph import GraphResponse, NodeSchema, EdgeSchema
from app.core.exceptions import SessionNotFoundError, NodeNotFoundError


@pytest.fixture
def mock_ai_service():
    """Mock AIService for testing GraphBuilder"""
    service = MagicMock()
    service.build_graph = AsyncMock()
    service.expand_node = AsyncMock()
    return service


@pytest.fixture
def graph_builder(mock_ai_service):
    """Create GraphBuilder instance with mocked AIService"""
    return GraphBuilder(mock_ai_service)


@pytest.fixture
def sample_graph():
    """Sample graph data returned from AI service"""
    return {
        "topic": "Quantum Computing",
        "nodes": [
            {
                "id": "1",
                "label": "Qubit",
                "definition": "Basic unit of quantum information",
                "importance": "core",
                "examples": ["Photon", "Electron"],
                "notes": ["Can be 0, 1, or both"],
                "tags": ["quantum", "physics"]
            },
            {
                "id": "2",
                "label": "Superposition",
                "definition": "Quantum state where particle exists in multiple states",
                "importance": "major",
                "examples": ["Schrödinger's cat"],
                "notes": [],
                "tags": ["quantum"]
            }
        ],
        "edges": [
            {
                "source": "1",
                "target": "2",
                "relation": "enables",
                "weight": 0.9
            }
        ]
    }


class TestGraphBuilderInit:
    def test_init_creates_instance(self, mock_ai_service):
        """Test GraphBuilder initialization"""
        builder = GraphBuilder(mock_ai_service)
        assert builder.ai == mock_ai_service
        assert builder.sessions == {}

    def test_init_with_ai_service(self, graph_builder, mock_ai_service):
        """Test that GraphBuilder stores AIService correctly"""
        assert graph_builder.ai is mock_ai_service


class TestBuildNodes:
    def test_build_nodes_converts_dicts_to_schemas(self, graph_builder, sample_graph):
        """Test _build_nodes converts dictionaries to NodeSchema objects"""
        nodes = graph_builder._build_nodes(sample_graph)
        
        assert len(nodes) == 2
        assert all(isinstance(node, NodeSchema) for node in nodes)
        assert nodes[0].id == "1"
        assert nodes[0].label == "Qubit"
        assert nodes[1].label == "Superposition"

    def test_build_nodes_empty_graph(self, graph_builder):
        """Test _build_nodes with empty graph"""
        empty_graph = {}
        nodes = graph_builder._build_nodes(empty_graph)
        assert nodes == []

    def test_build_nodes_preserves_all_fields(self, graph_builder, sample_graph):
        """Test that all NodeSchema fields are preserved"""
        nodes = graph_builder._build_nodes(sample_graph)
        node = nodes[0]
        
        assert node.id == "1"
        assert node.label == "Qubit"
        assert node.definition == "Basic unit of quantum information"
        assert node.importance == "core"
        assert node.examples == ["Photon", "Electron"]
        assert node.notes == ["Can be 0, 1, or both"]
        assert node.tags == ["quantum", "physics"]


class TestBuildEdges:
    def test_build_edges_converts_dicts_to_schemas(self, graph_builder, sample_graph):
        """Test _build_edges converts dictionaries to EdgeSchema objects"""
        edges = graph_builder._build_edges(sample_graph)
        
        assert len(edges) == 1
        assert all(isinstance(edge, EdgeSchema) for edge in edges)
        assert edges[0].source == "1"
        assert edges[0].target == "2"

    def test_build_edges_empty_graph(self, graph_builder):
        """Test _build_edges with empty graph"""
        empty_graph = {}
        edges = graph_builder._build_edges(empty_graph)
        assert edges == []

    def test_build_edges_preserves_all_fields(self, graph_builder, sample_graph):
        """Test that all EdgeSchema fields are preserved"""
        edges = graph_builder._build_edges(sample_graph)
        edge = edges[0]
        
        assert edge.source == "1"
        assert edge.target == "2"
        assert edge.relation == "enables"
        assert edge.weight == 0.9


@pytest.mark.asyncio
class TestBuild:
    async def test_build_creates_session(self, graph_builder, mock_ai_service, sample_graph):
        """Test that build() creates a new session"""
        mock_ai_service.build_graph.return_value = sample_graph
        
        result = await graph_builder.build("Quantum Computing", "en", 2, "url")
        
        assert isinstance(result, GraphResponse)
        assert result.session_id in graph_builder.sessions
        assert graph_builder.sessions[result.session_id] == sample_graph

    async def test_build_returns_graph_response(self, graph_builder, mock_ai_service, sample_graph):
        """Test that build() returns a valid GraphResponse"""
        mock_ai_service.build_graph.return_value = sample_graph
        
        result = await graph_builder.build("Quantum Computing", "en", 2, "url")
        
        assert isinstance(result, GraphResponse)
        assert result.topic == "Quantum Computing"
        assert len(result.nodes) == 2
        assert len(result.edges) == 1
        assert result.meta["source_type"] == "url"

    async def test_build_with_default_topic(self, graph_builder, mock_ai_service):
        """Test that build() uses text prefix as default topic"""
        graph_no_topic = {
            "nodes": [],
            "edges": []
        }
        mock_ai_service.build_graph.return_value = graph_no_topic
        text = "This is a very long text that should be truncated to 80 characters to serve as the topic"
        
        result = await graph_builder.build(text, "en", 2, "url")
        
        assert result.topic == text[:80]

    async def test_build_calls_ai_service(self, graph_builder, mock_ai_service, sample_graph):
        """Test that build() calls AIService.build_graph with correct arguments"""
        mock_ai_service.build_graph.return_value = sample_graph
        
        await graph_builder.build("Test text", "ru", 3, "term")
        
        mock_ai_service.build_graph.assert_called_once_with("Test text", "ru", 3, "term")


class TestGetSession:
    def test_get_session_returns_existing_session(self, graph_builder, sample_graph):
        """Test retrieving an existing session"""
        session_id = "test_session_123"
        graph_builder.sessions[session_id] = sample_graph
        
        result = graph_builder.get_session(session_id)
        
        assert result == sample_graph

    def test_get_session_raises_error_for_missing_session(self, graph_builder):
        """Test that get_session raises SessionNotFoundError for missing session"""
        with pytest.raises(SessionNotFoundError):
            graph_builder.get_session("nonexistent_session")


class TestGetNode:
    def test_get_node_returns_existing_node(self, graph_builder, sample_graph):
        """Test retrieving an existing node from a session"""
        session_id = "test_session"
        graph_builder.sessions[session_id] = sample_graph
        
        node = graph_builder.get_node(session_id, "1")
        
        assert node["id"] == "1"
        assert node["label"] == "Qubit"

    def test_get_node_raises_error_for_missing_node(self, graph_builder, sample_graph):
        """Test that get_node raises NodeNotFoundError for missing node"""
        session_id = "test_session"
        graph_builder.sessions[session_id] = sample_graph
        
        with pytest.raises(NodeNotFoundError):
            graph_builder.get_node(session_id, "nonexistent_node")

    def test_get_node_raises_error_for_missing_session(self, graph_builder):
        """Test that get_node raises SessionNotFoundError for missing session"""
        with pytest.raises(SessionNotFoundError):
            graph_builder.get_node("nonexistent_session", "node_id")


@pytest.mark.asyncio
class TestExpandNode:
    async def test_expand_node_extends_graph(self, graph_builder, sample_graph, mock_ai_service):
        """Test that expand_node extends the graph with new nodes and edges"""
        session_id = "test_session"
        graph_builder.sessions[session_id] = sample_graph.copy()
        
        new_data = {
            "new_nodes": [
                {
                    "id": "3",
                    "label": "Entanglement",
                    "definition": "Quantum correlation between particles",
                    "importance": "core",
                    "examples": [],
                    "notes": [],
                    "tags": []
                }
            ],
            "new_edges": [
                {
                    "source": "1",
                    "target": "3",
                    "relation": "exhibits",
                    "weight": 0.8
                }
            ]
        }
        mock_ai_service.expand_node.return_value = new_data
        
        result = await graph_builder.expand_node(session_id, "1")
        
        assert result == new_data
        assert len(graph_builder.sessions[session_id]["nodes"]) == 3
        assert len(graph_builder.sessions[session_id]["edges"]) == 2

    async def test_expand_node_calls_ai_service_with_correct_params(self, graph_builder, sample_graph, mock_ai_service):
        """Test that expand_node calls AIService with correct parameters"""
        session_id = "test_session"
        graph_builder.sessions[session_id] = sample_graph.copy()
        mock_ai_service.expand_node.return_value = {"new_nodes": [], "new_edges": []}
        
        await graph_builder.expand_node(session_id, "1")
        
        mock_ai_service.expand_node.assert_called_once_with(
            topic="Quantum Computing",
            node_id="1",
            label="Qubit",
            definition="Basic unit of quantum information"
        )

    async def test_expand_node_raises_error_for_missing_node(self, graph_builder, sample_graph):
        """Test that expand_node raises error for missing node"""
        session_id = "test_session"
        graph_builder.sessions[session_id] = sample_graph
        
        with pytest.raises(NodeNotFoundError):
            await graph_builder.expand_node(session_id, "nonexistent")

    async def test_expand_node_raises_error_for_missing_session(self, graph_builder):
        """Test that expand_node raises error for missing session"""
        with pytest.raises(SessionNotFoundError):
            await graph_builder.expand_node("nonexistent_session", "node_id")
