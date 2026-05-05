from functools import lru_cache
from app.services.ai import AIService
from app.services.graph_builder import GraphBuilder
from app.services.rag import RAGService
from app.services.scraper import ScraperService

'''To prevent circular imports, reusing the AI, overusing scraper etc. in multiple places,
we can use LRU cache for these dependencies'''


@lru_cache(maxsize=1)
def get_ai_service() -> AIService:
    return AIService()


@lru_cache(maxsize=1)
def get_graph_builder() -> GraphBuilder:
    return GraphBuilder(ai_service=get_ai_service()) #type: ignore


@lru_cache(maxsize=1)
def get_rag_service() -> RAGService:
    return RAGService()


@lru_cache(maxsize=1)
def get_scraper_service() -> ScraperService:
    return ScraperService()