import asyncio

from src.handoff.controller import HandoffController
from src.surface.playwright_surface import PlaywrightSurface


async def main():

    surface = PlaywrightSurface(
        headless=False
    )

    try:
        print("Starting browser...")

        await surface.start()

        await surface.navigate(
            "http://127.0.0.1:8000"
        )

        controller = HandoffController(
            surface
        )

        print(
            "\nAutomation reached a state "
            "requiring human intervention."
        )

        await controller.request_handoff(
            reason=(
                "Demo manual intervention: "
                "enter member ID 12345 and "
                "click Search manually."
            ),
            step_id="manual_demo_step",
        )

        print(
            "\nAutomation resumed."
        )

        observation = await surface.observe()

        print(
            "\n--- CURRENT PAGE AFTER HANDOFF ---"
        )

        print(
            observation["visible_text"]
        )

        controller.mark_completed()

        controller.save_events()

        await surface.screenshot(
            "evidence/handoff/"
            "handoff-final.png"
        )

        print(
            "\nSUCCESS: Human handoff "
            "completed on the same browser session."
        )

        print(
            "Evidence saved under "
            "evidence/handoff/"
        )

        await asyncio.sleep(3)

    finally:
        await surface.close()


if __name__ == "__main__":
    asyncio.run(main())