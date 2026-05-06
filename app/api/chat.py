from fastapi import APIRouter, Depends

from app.core.dependencies import get_graph_builder, get_rag_service, get_ai_service
from app.services.graph_builder import GraphBuilder
from app.services.rag import RAGService
from app.services.ai import AIService
from app.schemas.chat import ChatRequest, ChatResponse


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    builder: GraphBuilder = Depends(get_graph_builder),
    rag: RAGService = Depends(get_rag_service),
    ai: AIService = Depends(get_ai_service),
) -> ChatResponse:
    session = builder.get_session(request.session_id)
    topic = session["topic"]

    node_label = None
    node_definition = None
    if request.node_id:
        node = builder.get_node(request.session_id, request.node_id)
        node_label = node["label"]
        node_definition = node["definition"]

    rag_context = "\n\n".join(
        rag.query(session_id=request.session_id, question=request.question)
    )

    answer = await ai.answer(
        topic=topic,
        question=request.question,
        rag_context=rag_context,
        node_label=node_label or "",
        node_definition=node_definition or "",
    )

    return ChatResponse(answer=answer)