import pytest

from app.schemas.graph import EdgeSchema, GraphRequest, GraphResponse, NodeSchema
from pydantic import ValidationError


def test_graph_request_strips_input_and_detects_url():
    request = GraphRequest(input="  https://example.com  ")

    assert request.input == "https://example.com"
    assert request.is_url is True


def test_graph_request_rejects_too_short_input():
    with pytest.raises(ValidationError):
        GraphRequest(input="A")


def test_edge_schema_accepts_valid_weight():
    edge = EdgeSchema(source="a", target="b", relation="related", weight=0.75)

    assert edge.weight == 0.75


def test_edge_schema_rejects_out_of_range_weight():
    with pytest.raises(ValidationError):
        EdgeSchema(source="a", target="b", relation="related", weight=1.5)


def test_graph_response_contains_nodes_and_edges():
    node = NodeSchema(
        id="n1",
        label="Node 1",
        definition="A sample node",
        importance="core",
    )
    edge = EdgeSchema(source="n1", target="n2", relation="connects")
    response = GraphResponse(session_id="session-1", topic="Test Graph", nodes=[node], edges=[edge])

    assert response.session_id == "session-1"
    assert len(response.nodes) == 1
    assert response.nodes[0].id == "n1"
    assert len(response.edges) == 1
    assert response.edges[0].relation == "connects"
