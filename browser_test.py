import asyncio

from src.surface.playwright_surface import PlaywrightSurface


async def main():
    surface = PlaywrightSurface(headless=False)

    try:
        print("Starting browser...")
        await surface.start()

        print("Opening credit union app...")
        await surface.navigate("http://127.0.0.1:8000")

        observation = await surface.observe()

        print("\n--- INITIAL OBSERVATION ---")
        print("Title:", observation["title"])
        print("URL:", observation["url"])
        print("Visible text:")
        print(observation["visible_text"])
        print("Controls:")
        print(observation["controls"])

        print("\nEntering member ID 12345...")

        await surface.type_text(
            {
                "strategy": "label",
                "label": "Member ID"
            },
            "12345"
        )

        print("Clicking Search...")

        await surface.click(
            {
                "strategy": "role",
                "role": "button",
                "name": "Search"
            }
        )

        await surface.page.wait_for_load_state(
            "domcontentloaded"
        )

        result = await surface.observe()

        print("\n--- RESULT ---")
        print(result["visible_text"])

        await surface.screenshot(
            "evidence/browser-smoke-test.png"
        )

        print("\nSUCCESS: Browser automation completed.")

        await asyncio.sleep(3)

    finally:
        await surface.close()


if __name__ == "__main__":
    asyncio.run(main())