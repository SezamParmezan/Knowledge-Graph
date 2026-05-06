import httpx
import trafilatura

from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from bs4 import BeautifulSoup

from app.core.config import settings
from app.core.exceptions import ScrapingError


class ScraperService:
    def __init__(self):
        self._client = httpx.AsyncClient(
            timeout=settings.scraper_timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
            }
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
            no_fallback=False,
            include_formatting=False,
        )

        logger.debug(f"Extracted text length: {len(text) if text else 0} | preview: {text[:200] if text else 'None'}")
        if not text or len(text) < 100:
            soup = BeautifulSoup(response.text, 'html.parser')
            for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()
            text = soup.get_text(separator='\n', strip=True)

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

    