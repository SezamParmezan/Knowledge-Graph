from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str
    node_id: str | None = Field(
        default=None,
        description="If provided, the question will be asked in the context of this node.",
    )
    question: str = Field(..., min_length=3, max_length=1000)


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = Field(default_factory=list)
    suggested_nodes: list[str] = Field(default_factory=list)