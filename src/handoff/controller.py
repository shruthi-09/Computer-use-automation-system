from enum import Enum
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

from src.surface.playwright_surface import PlaywrightSurface


class ControlState(str, Enum):
    AUTOMATION = "automation"
    PAUSED = "paused"
    HUMAN = "human"
    RESUMING = "resuming"
    COMPLETED = "completed"


class HandoffController:

    def __init__(
        self,
        surface: PlaywrightSurface,
    ):
        self.surface = surface
        self.state = ControlState.AUTOMATION
        self.events: list[dict[str, Any]] = []

    async def request_handoff(
        self,
        reason: str,
        step_id: str | None = None,
    ) -> None:

        self.state = ControlState.PAUSED

        screenshot_path = (
            "evidence/handoff/"
            "handoff-request.png"
        )

        await self.surface.screenshot(
            screenshot_path
        )

        self._record_event(
            event="handoff_requested",
            reason=reason,
            step_id=step_id,
            screenshot=screenshot_path,
        )

        self.state = ControlState.HUMAN

        print("\n" + "=" * 60)
        print("HUMAN INTERVENTION REQUIRED")
        print("=" * 60)

        print(f"Reason: {reason}")

        if step_id:
            print(f"Current step: {step_id}")

        print(
            "\nAutomation is paused."
        )

        print(
            "Use the currently open browser window "
            "to complete the required manual action."
        )

        print(
            "\nWhen finished, return to this terminal "
            "and press ENTER."
        )

        print("=" * 60)

        input()

        await self.resume_automation()

    async def resume_automation(
        self,
    ) -> None:

        self.state = ControlState.RESUMING

        screenshot_path = (
            "evidence/handoff/"
            "handoff-resume.png"
        )

        await self.surface.screenshot(
            screenshot_path
        )

        self._record_event(
            event="handoff_completed",
            screenshot=screenshot_path,
        )

        self.state = ControlState.AUTOMATION

        print(
            "\nHuman handoff complete. "
            "Returning control to automation."
        )

    def mark_completed(
        self,
    ) -> None:

        self.state = ControlState.COMPLETED

        self._record_event(
            event="run_completed"
        )

    def _record_event(
        self,
        event: str,
        **details: Any,
    ) -> None:

        record = {
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "event": event,
            "control_state": self.state.value,
            **details,
        }

        self.events.append(record)

    def save_events(
        self,
        path: str = (
            "evidence/handoff/"
            "handoff-events.json"
        ),
    ) -> None:

        import json

        output_path = Path(path)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        output_path.write_text(
            json.dumps(
                self.events,
                indent=2
            ),
            encoding="utf-8",
        )