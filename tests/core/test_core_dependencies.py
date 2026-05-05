import pytest
from unittest.mock import patch
from app.core.dependencies import get_ai_service, get_graph_builder, get_rag_service, get_scraper_service
from app.services.ai import AIService
from app.services.graph_builder import GraphBuilder
from app.services.rag import RAGService
from app.services.scraper import ScraperService


@pytest.fixture(autouse=True)
def clear_caches():
    """Clear LRU caches before each test to ensure isolation."""
    get_ai_service.cache_clear()
    get_graph_builder.cache_clear()
    get_rag_service.cache_clear()
    get_scraper_service.cache_clear()


def test_get_ai_service_returns_ai_service_instance():
    with patch.dict('os.environ', {'AI_API_KEY': 'dummy_key'}):
        service = get_ai_service()
        assert isinstance(service, AIService)


def test_get_ai_service_caches_instance():
    with patch.dict('os.environ', {'AI_API_KEY': 'dummy_key'}):
        service1 = get_ai_service()
        service2 = get_ai_service()
        assert service1 is service2


def test_get_graph_builder_returns_graph_builder_instance():
    with patch.dict('os.environ', {'AI_API_KEY': 'dummy_key'}):
        builder = get_graph_builder()
        assert isinstance(builder, GraphBuilder)


def test_get_graph_builder_uses_cached_ai_service():
    with patch.dict('os.environ', {'AI_API_KEY': 'dummy_key'}):
        ai_service = get_ai_service()
        builder = get_graph_builder()
        assert builder.ai is ai_service


def test_get_graph_builder_caches_instance():
    with patch.dict('os.environ', {'AI_API_KEY': 'dummy_key'}):
        builder1 = get_graph_builder()
        builder2 = get_graph_builder()
        assert builder1 is builder2


def test_get_rag_service_returns_rag_service_instance():
    service = get_rag_service()
    assert isinstance(service, RAGService)


def test_get_rag_service_caches_instance():
    service1 = get_rag_service()
    service2 = get_rag_service()
    assert service1 is service2


def test_get_scraper_service_returns_scraper_service_instance():
    service = get_scraper_service()
    assert isinstance(service, ScraperService)


def test_get_scraper_service_caches_instance():
    service1 = get_scraper_service()
    service2 = get_scraper_service()
    assert service1 is service2