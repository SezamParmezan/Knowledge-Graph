'''Endpoint for nodes to get info and expand chosen node'''

from fastapi import APIRouter, Depends

from app.core.dependencies import get_graph_builder
from app.services.graph_builder import GraphBuilder
from app.schemas.nodes import NodeExpandRequest, NodeDetailResponse


router = APIRouter(prefix="/api/nodes", tags=["nodes"])


@router.get("/{session_id}/{node_id}", response_model=NodeDetailResponse)
async def get_node_info(
    session_id: str,
    node_id: str,
    builder: GraphBuilder = Depends(get_graph_builder),
):
    
    return builder.get_node(session_id, node_id)


@router.post("/expand")
async def expand_node(
        request: NodeExpandRequest,
        builder: GraphBuilder = Depends(get_graph_builder),
    ) -> dict:

    return await builder.expand_node(
        session_id=request.session_id,
        node_id=request.node_id,
    )