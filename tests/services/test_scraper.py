import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.scraper import ScraperService
from app.core.exceptions import ScrapingError


@pytest_asyncio.fixture
async def scraper_service():
    service = ScraperService()
    yield service
    await service._client.aclose()


@pytest.mark.asyncio
async def test_fetch_success(scraper_service):
    with patch('app.services.scraper.trafilatura.extract') as mock_extract:
        mock_extract.return_value = "Extracted content" * 100
        with patch.object(scraper_service._client, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.text = "<html>Test</html>"
            mock_get.return_value = mock_response
            
            result = await scraper_service.fetch("http://example.com")
            assert "Extracted content" in result
            assert len(result) > 100


@pytest.mark.asyncio
async def test_fetch_http_error(scraper_service):
    with patch.object(scraper_service._client, 'get') as mock_get:
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock(side_effect=Exception("404"))
        mock_get.return_value = mock_response
        
        with pytest.raises(ScrapingError):
            await scraper_service.fetch("http://example.com/notfound")


@pytest.mark.asyncio
async def test_fetch_empty_content(scraper_service):
    with patch('app.services.scraper.trafilatura.extract') as mock_extract:
        mock_extract.return_value = "Short"
        with patch.object(scraper_service._client, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.text = "<html></html>"
            mock_get.return_value = mock_response
            
            with pytest.raises(ScrapingError):
                await scraper_service.fetch("http://example.com")
