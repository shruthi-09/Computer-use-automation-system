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
            "\nTesting PERMISSION_DENIED "
            "hard failure..."
        )

        result = await executor.run(
            artifact,
            {
                "member_id": "55555"
            }
        )

        print("\n--- REPLAY RESULT ---")

        print(
            result.model_dump_json(
                indent=2
            )
        )

        print(
            "\nStatus:",
            result.status.value
        )

        print(
            "Error code:",
            result.error.code
            if result.error
            else None
        )

        print(
            "LLM calls:",
            result.llm_calls
        )

        if (
            result.status.value == "failure"
            and result.error
            and result.error.code
            == "PERMISSION_DENIED"
            and result.llm_calls == 0
        ):
            print(
                "\nSUCCESS: Permission denied "
                "was correctly classified as "
                "a hard failure."
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