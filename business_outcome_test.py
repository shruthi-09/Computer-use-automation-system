import asyncio

from src.artifacts.store import load_artifact
from src.replay.executor import ReplayExecutor
from src.surface.playwright_surface import PlaywrightSurface


async def main():

    artifact = load_artifact(
        "artifacts/examples/"
        "lookup_savings_balance-v1.json"
    )

    surface = PlaywrightSurface(
        headless=False
    )

    try:
        print("Starting browser...")

        await surface.start()

        executor = ReplayExecutor(
            surface
        )

        print(
            "\nTesting MEMBER_NOT_FOUND "
            "business outcome..."
        )

        result = await executor.run(
            artifact,
            {
                "member_id": "99999"
            }
        )

        print("\n--- REPLAY RESULT ---")

        print(
            result.model_dump_json(
                indent=2
            )
        )

        await surface.screenshot(
            "evidence/replay/"
            "member-not-found.png"
        )

        print(
            "\nStatus:",
            result.status.value
        )

        print(
            "Business outcome:",
            result.business_outcome
        )

        print(
            "LLM calls:",
            result.llm_calls
        )

        if (
            result.status.value
            == "business_outcome"
            and result.business_outcome
            == "MEMBER_NOT_FOUND"
            and result.llm_calls == 0
        ):
            print(
                "\nSUCCESS: Member not found "
                "was correctly classified as "
                "a business outcome."
            )

        else:
            print(
                "\nTEST FAILED: Unexpected result."
            )

        await asyncio.sleep(3)

    finally:
        await surface.close()


if __name__ == "__main__":
    asyncio.run(main())