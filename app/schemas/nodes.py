from pydantic import BaseModel, Field
from typing import Literal

class NodeDetailResponse(BaseModel):
    '''Response model for node details.'''
    id: str
    label: str
    definition: str
    importance: Literal["core", "major", "minor"]
    examples: list[str]
    notes: list[str]
    tags: list[str]
    related_nodes: list[str] #related node ids


class NodeExpandRequest(BaseModel):
    '''Request model for expanding a node.'''
    session_id: str
    node_id: str
    depth: int = Field(default=1, ge=1, le=2)


class NodeExpandResponse(BaseModel):
    new_nodes: list[dict]
    new_edges: list[dict]