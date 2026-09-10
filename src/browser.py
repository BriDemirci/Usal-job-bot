import asyncio
import random
from typing import List, Optional
from playwright.async_api import async_playwright, Browser, Page, Locator

class ChromeConnector:
    def __init__(self, cdp_url: str = "http://localhost:9222"):
        self.cdp_url = cdp_url
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.active_page: Optional[Page] = None

    async def connect(self) -> Page:
        self.playwright = await async_playwright().start()
        try:
            self.browser = await self.playwright.chromium.connect_over_cdp(self.cdp_url)
        except Exception as e:
            raise ConnectionError(
                f"No se pudo conectar a Chrome en {self.cdp_url}. "
                "Asegurate de haber ejecutado launch_chrome.bat y que Chrome este abierto con el puerto 9222."
            ) from e

        # Buscar pestaña relevante o usar la primera activa
        page = await self.find_target_tab(["usal", "empleo", "job", "career"])
        if not page and self.browser.contexts and self.browser.contexts[0].pages:
            page = self.browser.contexts[0].pages[0]
            await page.bring_to_front()

        self.active_page = page
        return page

    async def find_target_tab(self, keywords: List[str]) -> Optional[Page]:
        if not self.browser:
            return None
        for context in self.browser.contexts:
            for page in context.pages:
                url_lower = page.url.lower()
                title = await page.title() if hasattr(page, "title") else ""
                title_lower = title.lower() if isinstance(title, str) else ""
                if any(kw in url_lower or kw in title_lower for kw in keywords):
                    await page.bring_to_front()
                    self.active_page = page
                    return page
        return None

    async def human_delay(self, min_s: float = 1.0, max_s: float = 2.5) -> None:
        delay = random.uniform(min_s, max_s)
        await asyncio.sleep(delay)

    async def safe_click(self, target: Locator | str) -> bool:
        if not self.active_page:
            return False
        locator = self.active_page.locator(target) if isinstance(target, str) else target
        if await locator.count() > 0:
            await locator.first.scroll_into_view_if_needed()
            await self.human_delay(0.3, 0.6)
            await locator.first.click()
            await self.human_delay(0.4, 0.8)
            return True
        return False

    async def close(self) -> None:
        if self.playwright:
            await self.playwright.stop()
