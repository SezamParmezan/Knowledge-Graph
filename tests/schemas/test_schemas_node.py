import pytest

from app.schemas.nodes import NodeDetailResponse, NodeExpandRequest, NodeExpandResponse
from pydantic import ValidationError


def test_node_detail_response_contains_all_fields():
    detail = NodeDetailResponse(
        node_id="n1",
        label="Node One",
        definition="Details for node one.",
        importance="major",
        examples=["Example 1"],
        notes=["Note A"],
        tags=["tag1"],
        related_nodes=["n2", "n3"],
    )

    assert detail.node_id == "n1"
    assert detail.importance == "major"
    assert detail.related_nodes == ["n2", "n3"]


def test_node_expand_request_validates_depth_range():
    request = NodeExpandRequest(session_id="session-1", node_id="n1", depth=2)

    assert request.depth == 2


def test_node_expand_request_rejects_invalid_depth():
    with pytest.raises(ValidationError):
        NodeExpandRequest(session_id="session-1", node_id="n1", depth=0)


def test_node_expand_response_accepts_lists():
    response = NodeExpandResponse(new_nodes=[{"id": "n2"}], new_edges=[{"source": "n1", "target": "n2"}])

    assert response.new_nodes[0]["id"] == "n2"
    assert response.new_edges[0]["source"] == "n1"
