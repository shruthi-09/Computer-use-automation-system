from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright

from src.surface.base import ComputerSurface


class PlaywrightSurface(ComputerSurface):

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    async def start(self) -> None:
        self.playwright = await async_playwright().start()

        self.browser = await self.playwright.chromium.launch(
            headless=self.headless
        )

        self.context = await self.browser.new_context()

        self.page = await self.context.new_page()

    async def navigate(self, target: str) -> None:
        await self.page.goto(
            target,
            wait_until="domcontentloaded"
        )

    async def observe(self) -> dict[str, Any]:
        title = await self.page.title()
        url = self.page.url

        visible_text = await self.page.locator("body").inner_text()

        controls = await self.page.locator(
            "input, button, select, textarea, a"
        ).evaluate_all(
            """
            elements => elements.map((el, index) => ({
                index: index,
                tag: el.tagName.toLowerCase(),
                type: el.getAttribute('type'),
                name: el.getAttribute('name'),
                id: el.id || null,
                text: (el.innerText || el.value || '').trim(),
                aria_label: el.getAttribute('aria-label'),
                placeholder: el.getAttribute('placeholder')
            }))
            """
        )

        return {
            "title": title,
            "url": url,
            "visible_text": visible_text,
            "controls": controls,
        }

    async def click(self, target: dict[str, Any]) -> None:
        strategy = target.get("strategy")

        if strategy == "role":
            locator = self.page.get_by_role(
                target["role"],
                name=target.get("name")
            )

        elif strategy == "text":
            locator = self.page.get_by_text(
                target["text"],
                exact=True
            )

        elif strategy == "css":
            locator = self.page.locator(
                target["selector"]
            )

        else:
            raise ValueError(
                f"Unsupported click strategy: {strategy}"
            )

        await locator.click()

    async def type_text(
        self,
        target: dict[str, Any],
        value: str
    ) -> None:

        strategy = target.get("strategy")

        if strategy == "label":
            locator = self.page.get_by_label(
                target["label"]
            )

        elif strategy == "css":
            locator = self.page.locator(
                target["selector"]
            )

        elif strategy == "placeholder":
            locator = self.page.get_by_placeholder(
                target["placeholder"]
            )

        else:
            raise ValueError(
                f"Unsupported type strategy: {strategy}"
            )

        await locator.fill(value)

    async def screenshot(self, path: str) -> None:
        screenshot_path = Path(path)

        screenshot_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        await self.page.screenshot(
            path=str(screenshot_path),
            full_page=True
        )

    async def close(self) -> None:
        if self.context:
            await self.context.close()

        if self.browser:
            await self.browser.close()

        if self.playwright:
            await self.playwright.stop()