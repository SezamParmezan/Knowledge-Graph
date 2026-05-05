from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import kg_exception_handler, unhandled_exception_handler, KGException
from app.core.logging import setup_logging
from app.core.dependencies import get_scraper_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.ensure_dirs()
    setup_logging()

    yield

    await get_scraper_service().close()


BASE_DIR = Path(__file__).parent.parent

app = FastAPI(lifespan=lifespan)
app.add_exception_handler(KGException, kg_exception_handler) #type: ignore
app.add_exception_handler(Exception, unhandled_exception_handler)
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/")
async def selection_page(request: Request):
    return templates.TemplateResponse("main.html", {"request": request})


@app.get("/graph/{session_id}")
async def graph_page(request: Request, session_id: str):
    return templates.TemplateResponse("graph.html", {"request": request, "session_id": session_id})