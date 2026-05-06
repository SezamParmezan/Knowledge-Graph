from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import kg_exception_handler, unhandled_exception_handler, KGException
from app.core.logging import setup_logging
from app.core.dependencies import get_scraper_service

from app.api.graph import router as graph_router
from app.api.chat import router as chat_router
from app.api.nodes import router as nodes_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.ensure_dirs()
    setup_logging()

    yield

    await get_scraper_service().close()


BASE_DIR = Path(__file__).parent.parent

app = FastAPI(lifespan=lifespan)

#Exceptions
app.add_exception_handler(KGException, kg_exception_handler) #type: ignore
app.add_exception_handler(Exception, unhandled_exception_handler)

#Static files and templates
templates = Jinja2Templates(directory=BASE_DIR / "templates")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

#Endpoints
app.include_router(graph_router)
app.include_router(nodes_router)
app.include_router(chat_router)


@app.get("/")
async def selection_page(request: Request):
    return templates.TemplateResponse(request, "main.html")


@app.get("/graph/{session_id}")
async def graph_page(request: Request, session_id: str):
    return templates.TemplateResponse(request, "graph.html", {"session_id": session_id})  # type: ignore