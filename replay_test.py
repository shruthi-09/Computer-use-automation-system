import asyncio
import json
from pathlib import Path

from src.artifacts.store import load_artifact
from src.observability.logger import RunLogger
from src.replay.executor import ReplayExecutor
from src.surface.playwright_surface import PlaywrightSurface


async def main():

    artifact_path = (
        "artifacts/examples/"
        "lookup_savings_balance-v1.json"
    )

    evidence_dir = Path(
        "evidence/replay"
    )

    evidence_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    events_path = (
        evidence_dir
        / "events.jsonl"
    )

    # Start this final evidence run with a clean log.
    if events_path.exists():
        events_path.unlink()

    logger = RunLogger(
        run_id="replay-001",
        mode="replay",
        output_path=str(
            events_path
        ),
    )

    print(
        "Loading capability artifact..."
    )

    artifact = load_artifact(
        artifact_path
    )

    print(
        "Capability:",
        artifact.capability_name
    )

    logger.log(
        "run_started",
        capability_name=(
            artifact.capability_name
        ),
        artifact_path=artifact_path,
    )

    logger.log(
        "artifact_loaded",
        capability_name=(
            artifact.capability_name
        ),
        schema_version=(
            artifact.schema_version
        ),
        step_count=len(
            artifact.steps
        ),
    )

    surface = PlaywrightSurface(
        headless=False
    )

    try:
        print(
            "Starting browser..."
        )

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

        print(
            "\n--- REPLAY RESULT ---"
        )

        print(
            result.model_dump_json(
                indent=2
            )
        )

        result_path = (
            evidence_dir
            / "replay-result.json"
        )

        result_path.write_text(
            result.model_dump_json(
                indent=2
            ),
            encoding="utf-8",
        )

        await surface.screenshot(
            "evidence/replay/"
            "successful-replay.png"
        )

        logger.log(
            "replay_completed",
            status=result.status.value,
            capability_name=(
                result.capability_name
            ),
            completed_steps=(
                result.completed_steps
            ),
            output_names=list(
                result.outputs.keys()
            ),
            llm_calls=(
                result.llm_calls
            ),
        )

        print(
            "\nLLM calls during replay:",
            result.llm_calls
        )

        if (
            result.status.value
            == "success"
            and result.outputs.get(
                "savings_balance"
            )
            == "$4,821.77"
            and result.llm_calls == 0
        ):
            print(
                "\nSUCCESS: Deterministic "
                "replay passed."
            )

            print(
                "\nReplay evidence saved:"
            )

            print(
                "evidence/replay/"
                "replay-result.json"
            )

            print(
                "evidence/replay/"
                "events.jsonl"
            )

        else:
            print(
                "\nReplay completed, but "
                "the expected result "
                "was not returned."
            )

        await asyncio.sleep(3)

    except Exception as exc:

        logger.log(
            "replay_test_failed",
            error_type=(
                type(exc).__name__
            ),
            message=str(exc),
        )

        raise

    finally:
        await surface.close()


if __name__ == "__main__":
    asyncio.run(main())