from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright

from src.surface.base import ComputerSurface


class PlaywrightSurface(ComputerSurface):

    def __init__(
        self,
        headless: bool = False,
    ):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    async def start(self) -> None:

        self.playwright = (
            await async_playwright().start()
        )

        self.browser = (
            await self.playwright.chromium.launch(
                headless=self.headless
            )
        )

        self.context = (
            await self.browser.new_context()
        )

        self.page = (
            await self.context.new_page()
        )

    async def navigate(
        self,
        target: str,
    ) -> None:

        await self.page.goto(
            target,
            wait_until="domcontentloaded",
        )

    async def observe(
        self,
    ) -> dict[str, Any]:

        title = await self.page.title()
        url = self.page.url

        visible_text = (
            await self.page
            .locator("body")
            .inner_text()
        )

        controls = (
            await self.page.locator(
                "input, button, select, textarea, a"
            ).evaluate_all(
                """
                elements => elements.map(
                    (el, index) => {
                        const tag =
                            el.tagName.toLowerCase();

                        const type =
                            el.getAttribute('type');

                        let inferredRole =
                            el.getAttribute('role');

                        if (!inferredRole) {
                            if (tag === 'button') {
                                inferredRole = 'button';
                            } else if (
                                tag === 'input'
                                && (
                                    type === 'text'
                                    || !type
                                )
                            ) {
                                inferredRole = 'textbox';
                            } else if (
                                tag === 'select'
                            ) {
                                inferredRole = 'combobox';
                            } else if (
                                tag === 'a'
                            ) {
                                inferredRole = 'link';
                            }
                        }

                        let label = null;

                        if (
                            el.labels
                            && el.labels.length > 0
                        ) {
                            label = Array.from(
                                el.labels
                            )
                            .map(
                                item =>
                                    item.innerText.trim()
                            )
                            .join(' ');
                        }

                        return {
                            index: index,
                            tag: tag,
                            type: type,
                            role: inferredRole,
                            name:
                                el.getAttribute('name'),
                            id:
                                el.id || null,
                            label: label,
                            text: (
                                el.innerText
                                || el.value
                                || ''
                            ).trim(),
                            aria_label:
                                el.getAttribute(
                                    'aria-label'
                                ),
                            placeholder:
                                el.getAttribute(
                                    'placeholder'
                                )
                        };
                    }
                )
                """
            )
        )

        return {
            "title": title,
            "url": url,
            "visible_text": visible_text,
            "controls": controls,
        }

    async def _first_existing(
        self,
        candidates,
    ):

        for candidate in candidates:

            if candidate is None:
                continue

            try:
                if await candidate.count() > 0:
                    return candidate.first

            except Exception:
                continue

        return None

    async def click(
        self,
        target: dict[str, Any],
    ) -> None:

        strategy = target.get("strategy")

        role = target.get("role")
        name = target.get("name")
        label = target.get("label")
        text = target.get("text")
        selector = target.get("selector")
        placeholder = target.get(
            "placeholder"
        )

        candidates = []

        if strategy == "role":

            if role:
                candidates.append(
                    self.page.get_by_role(
                        role,
                        name=name
                        if name
                        else None,
                    )
                )

            # Model sometimes provides:
            # strategy=role, name=Search
            # but forgets role=button.
            if name:
                candidates.append(
                    self.page.get_by_role(
                        "button",
                        name=name,
                    )
                )

                candidates.append(
                    self.page.get_by_text(
                        name,
                        exact=True,
                    )
                )

        elif strategy == "text":

            if text:
                candidates.append(
                    self.page.get_by_text(
                        text,
                        exact=True,
                    )
                )

        elif strategy == "label":

            if label:
                candidates.append(
                    self.page.get_by_label(
                        label,
                        exact=False,
                    )
                )

        elif strategy == "css":

            if selector:
                candidates.append(
                    self.page.locator(
                        selector
                    )
                )

        elif strategy == "placeholder":

            if placeholder:
                candidates.append(
                    self.page.get_by_placeholder(
                        placeholder
                    )
                )

        # Universal semantic fallbacks.

        if name:
            candidates.append(
                self.page.get_by_role(
                    "button",
                    name=name,
                )
            )

            candidates.append(
                self.page.get_by_text(
                    name,
                    exact=True,
                )
            )

        if text:
            candidates.append(
                self.page.get_by_text(
                    text,
                    exact=True,
                )
            )

        if label:
            candidates.append(
                self.page.get_by_label(
                    label,
                    exact=False,
                )
            )

        if selector:
            candidates.append(
                self.page.locator(
                    selector
                )
            )

        locator = await self._first_existing(
            candidates
        )

        if locator is None:
            raise ValueError(
                "Unable to resolve click target: "
                f"{target}"
            )

        await locator.click()

    async def type_text(
        self,
        target: dict[str, Any],
        value: str,
    ) -> None:

        strategy = target.get("strategy")

        role = target.get("role")
        name = target.get("name")
        label = target.get("label")
        selector = target.get("selector")
        placeholder = target.get(
            "placeholder"
        )

        candidates = []

        if strategy == "label" and label:

            candidates.append(
                self.page.get_by_label(
                    label,
                    exact=False,
                )
            )

            normalized = (
                label
                .replace("_", " ")
                .replace("-", " ")
                .strip()
            )

            candidates.append(
                self.page.get_by_label(
                    normalized,
                    exact=False,
                )
            )

            safe_label = label.replace(
                '"',
                '\\"',
            )

            candidates.append(
                self.page.locator(
                    f'[id="{safe_label}"]'
                )
            )

            candidates.append(
                self.page.locator(
                    f'[name="{safe_label}"]'
                )
            )

        elif (
            strategy == "placeholder"
            and placeholder
        ):

            candidates.append(
                self.page.get_by_placeholder(
                    placeholder
                )
            )

        elif strategy == "css" and selector:

            candidates.append(
                self.page.locator(
                    selector
                )
            )

        elif strategy == "role":

            if role:
                candidates.append(
                    self.page.get_by_role(
                        role,
                        name=name
                        if name
                        else None,
                    )
                )

            if name:
                candidates.append(
                    self.page.get_by_role(
                        "textbox",
                        name=name,
                    )
                )

        # Universal input fallbacks.

        if label:
            normalized = (
                label
                .replace("_", " ")
                .replace("-", " ")
                .strip()
            )

            candidates.append(
                self.page.get_by_label(
                    normalized,
                    exact=False,
                )
            )

        if name:

            safe_name = name.replace(
                '"',
                '\\"',
            )

            candidates.append(
                self.page.locator(
                    f'[name="{safe_name}"]'
                )
            )

            candidates.append(
                self.page.locator(
                    f'[id="{safe_name}"]'
                )
            )

        if placeholder:
            candidates.append(
                self.page.get_by_placeholder(
                    placeholder
                )
            )

        locator = await self._first_existing(
            candidates
        )

        if locator is None:
            raise ValueError(
                "Unable to resolve input target: "
                f"{target}"
            )

        await locator.fill(
            value
        )

    async def screenshot(
        self,
        path: str,
    ) -> None:

        screenshot_path = Path(
            path
        )

        screenshot_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        await self.page.screenshot(
            path=str(
                screenshot_path
            ),
            full_page=True,
        )

    async def close(
        self,
    ) -> None:

        if self.context:
            await self.context.close()

        if self.browser:
            await self.browser.close()

        if self.playwright:
            await self.playwright.stop()