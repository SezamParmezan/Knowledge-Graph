from pydantic import BaseModel, Field, field_validator
from typing import Literal
import re


class GraphRequest(BaseModel):
    input: str = Field(
        ...,
        min_length = 2,
        max_length = 2048,
        description = "Enter the URL or term to build your knowledge graph!",
        examples = ["Black hole", "https://arxiv.org/abs/1706.03762"]
    )

    depth: int = Field(default = 2, ge = 1, le = 3)
    language: Literal["en", "ru"] = Field(default = "en")

    @field_validator("input")
    @classmethod
    def strip_input(cls, v: str) -> str:
        return v.strip()
    

    @property
    def is_url(self) -> bool:
        return self.input.startswith(("http://", "https://"))


class NodeSchema(BaseModel):
    id: str
    label: str
    definition: str
    importance: Literal["core", "major", "minor"]
    examples: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class EdgeSchema(BaseModel):
    source: str
    target: str
    relation: str
    weight: float = Field(default=1.0, ge=0.0, le=1.0)


class GraphResponse(BaseModel):
    session_id: str
    topic: str
    nodes: list[NodeSchema]
    edges: list[EdgeSchema]
    meta: dict = Field(default_factory=dict)