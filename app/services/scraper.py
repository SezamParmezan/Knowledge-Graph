import httpx
import trafilatura

from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import settings
from app.core.exceptions import ScrapingError


class ScraperService:
    def __init__(self):
        self._client = httpx.AsyncClient(
            timeout=settings.scraper_timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; KnowledgeGraphBot/1.0)"
            },
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )

    async def fetch(self, url: str) -> str:
        logger.info(f"Scraping: {url}")
        try:
            response = await self._client.get(url)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise ScrapingError(url, f"HTTP {e.response.status_code}")
        except httpx.RequestError as e:
            raise ScrapingError(url, str(e))

        text = trafilatura.extract(
            response.text,
            include_comments=False,
            include_tables=True,
            favor_recall=True,
        )

        if not text or len(text) < 100:
            raise ScrapingError(url, "Failed to extract meaningful content")

        text = self._clean(text)
        logger.info(f"Scraped {len(text)} chars from {url}")
        return text
    

    async def close(self) -> None:
        await self._client.aclose()

    
    @staticmethod
    def _clean(text: str) -> str:
        import re
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)
        return text.strip()[:settings.scraper_max_chars]

    