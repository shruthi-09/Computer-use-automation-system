import asyncio
import json
from pathlib import Path

from src.agent.discovery import DiscoveryRunner
from src.agent.planner import LLMPlanner
from src.artifacts.recorder import ArtifactRecorder
from src.artifacts.store import save_artifact
from src.safety.policy import SafetyGuard
from src.surface.playwright_surface import PlaywrightSurface


async def main():

    goal = (
        "Look up member 12345 and return "
        "their current savings balance."
    )

    target = "http://127.0.0.1:8000"

    surface = PlaywrightSurface(
        headless=False
    )

    try:
        print("Starting browser...")

        await surface.start()

        planner = LLMPlanner()

        safety = SafetyGuard()

        runner = DiscoveryRunner(
            surface=surface,
            planner=planner,
            safety=safety,
            max_steps=8,
        )

        print(
            "\nStarting genuine "
            "LLM discovery run..."
        )

        print("\nGoal:")
        print(goal)

        result = await runner.run(
            goal=goal,
            target=target,
        )

        print("\n--- DISCOVERY RESULT ---")

        print(
            json.dumps(
                result,
                indent=2,
            )
        )

        evidence_dir = Path(
            "evidence/discovery"
        )

        evidence_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        result_path = (
            evidence_dir
            / "discovery-result.json"
        )

        result_path.write_text(
            json.dumps(
                result,
                indent=2,
            ),
            encoding="utf-8",
        )

        await surface.screenshot(
            "evidence/discovery/"
            "discovery-final.png"
        )

        print(
            "\nDiscovery evidence saved to:"
        )

        print(
            "evidence/discovery/"
        )

        print(
            "\nLLM calls:",
            result.get("llm_calls")
        )

        if result.get("status") == "success":

            recorder = ArtifactRecorder()

            artifact = (
                recorder.build_from_discovery(
                    result
                )
            )

            artifact_path = (
                "artifacts/examples/"
                "lookup_savings_balance-v1.json"
            )

            save_artifact(
                artifact,
                artifact_path,
            )

            print(
                "\nCapability artifact created "
                "from discovery history:"
            )

            print(
                artifact_path
            )

            print(
                "\nRecorded steps:"
            )

            for step in artifact.steps:
                print(
                    f"- {step.id}: "
                    f"{step.action}"
                )

            print(
                "\nSUCCESS: Genuine "
                "LLM-driven discovery completed "
                "and artifact was generated."
            )

        else:
            print(
                "\nDiscovery did not "
                "fully complete."
            )

        await asyncio.sleep(3)

    finally:
        await surface.close()


if __name__ == "__main__":
    asyncio.run(main())