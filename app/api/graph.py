import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.core.dependencies import get_graph_builder, get_scraper_service, get_rag_service
from app.services.graph_builder import GraphBuilder
from app.services.scraper import ScraperService
from app.services.rag import RAGService
from app.schemas.graph import GraphRequest, GraphResponse


router = APIRouter(prefix="/graph", tags=["graph"])


async def build_stream(request: GraphRequest, builder: GraphBuilder, scraper: ScraperService, rag: RAGService):
    def event(step: str, payload: dict = {}) -> str:
        return f"data: {json.dumps({'step': step, **payload})}\n\n"

    try:
        if request.is_url:
            yield event("scraping", {"message": "Reading article..."})
            text = await scraper.fetch(request.input)
            source_type = "url"
        else:
            yield event("resolving", {"message": "Analysing term..."})
            text = request.input
            source_type = "term"

        yield event("building", {"message": "Building knowledge graph..."})
        graph = await builder.build(
            text=text,
            language=request.language,
            depth=request.depth,
            source_type=source_type,
        )

        if request.is_url:
            yield event("indexing", {"message": "Indexing source for chat..."})
            rag.index(session_id=graph.session_id, text=text)

        yield event("done", {"graph": graph.model_dump()})

    except Exception as e:
        yield event("error", {"message": str(e)})


@router.post("/build")
async def build_graph(
    request: GraphRequest,
    builder: GraphBuilder = Depends(get_graph_builder),
    scraper: ScraperService = Depends(get_scraper_service),
    rag: RAGService = Depends(get_rag_service),
) -> StreamingResponse:
    return StreamingResponse(
        build_stream(request, builder, scraper, rag),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{session_id}", response_model=GraphResponse)
async def get_graph(
    session_id: str,
    builder: GraphBuilder = Depends(get_graph_builder),
) -> GraphResponse:
    return GraphResponse(**builder.get_session(session_id))