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


    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True,)
    async def fetch(self, url: str) -> str:
        logger.info(f"Scraping: {url}")
        html = None

        try:
            response = await self._client.get(url)
            response.raise_for_status()
            html = response.text
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                #playwright fallback for 403 errors
                html = await self._fetch_with_playwright(url)
            else:
                raise ScrapingError(url, f"HTTP {e.response.status_code}")
        except httpx.RequestError as e:
            raise ScrapingError(url, str(e))

        text = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=True,
            favor_recall=True,
            no_fallback=False,
            include_formatting=False,
        )

        #BeautifulSoul fallback
        if not text or len(text) < 100:
            logger.debug("trafilatura failed, trying BS4")
            soup = BeautifulSoup(html, 'html.parser')
            for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()
            text = soup.get_text(separator='\n', strip=True)

        #Plan B - playwright fallback
        if not text or len(text) < 100:
            logger.debug("BS4 failed, trying Playwright")
            html = await self._fetch_with_playwright(url)
            text = trafilatura.extract(html, favor_recall=True) or ''

        #Plan C - return error
        if not text or len(text) < 100:
            raise ScrapingError(url, "Failed to extract meaningful content")

        text = self._clean(text)
        text = self._smart_trim(text)
        logger.info(f"Scraped {len(text)} chars from {url}")
        return text


    async def _fetch_with_playwright(self, url: str) -> str:
        import asyncio
        logger.info(f"Falling back to Playwright | url={url}")
        return await asyncio.to_thread(self._playwright_sync, url)
    

    async def close(self) -> None:
        await self._client.aclose()

    
    @staticmethod
    def _clean(text: str) -> str:
        import re
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)
        return text.strip()


    @staticmethod
    def _smart_trim(text: str, max_chars: int = settings.scraper_max_chars) -> str:
        '''So the main problem is that in URL scrapping the input is too long'''
        '''And this function is to trim the text to the max length allowed by the model, but also to keep the most important parts of the text'''
        
        if len(text) <= max_chars:
            return text
        third = max_chars // 3
        start = text[:third]
        mid_start = len(text) // 2 - third // 2
        middle = text[mid_start:mid_start + third]
        end = text[-third:]
        return f"{start}\n\n[...]\n\n{middle}\n\n[...]\n\n{end}"

    @staticmethod
    def _playwright_sync(url: str) -> str:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until='networkidle', timeout=30000)
            html = page.content()
            browser.close()
            return html