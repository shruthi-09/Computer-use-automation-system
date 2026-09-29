import asyncio

from src.artifacts.store import load_artifact
from src.replay.executor import ReplayExecutor
from src.surface.playwright_surface import PlaywrightSurface


async def main():

    artifact_path = (
        "artifacts/examples/"
        "lookup_savings_balance-v1.json"
    )

    print("Loading capability artifact...")

    artifact = load_artifact(
        artifact_path
    )

    print(
        "Capability:",
        artifact.capability_name
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
            "\nRunning deterministic replay..."
        )

        result = await executor.run(
            artifact,
            {
                "member_id": "12345"
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
            "successful-replay.png"
        )

        print(
            "\nLLM calls during replay:",
            result.llm_calls
        )

        if (
            result.status.value == "success"
            and result.outputs.get(
                "savings_balance"
            ) == "$4,821.77"
            and result.llm_calls == 0
        ):
            print(
                "\nSUCCESS: Deterministic "
                "replay passed."
            )
        else:
            print(
                "\nReplay completed, but the "
                "expected result was not returned."
            )

        await asyncio.sleep(3)

    finally:
        await surface.close()


if __name__ == "__main__":
    asyncio.run(main())