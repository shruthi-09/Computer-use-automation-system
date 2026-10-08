from typing import Any

from src.agent.planner import LLMPlanner
from src.safety.policy import (
    SafetyGuard,
    SafetyViolation,
)
from src.safety.redaction import redact_data
from src.surface.playwright_surface import PlaywrightSurface


class DiscoveryRunner:

    def __init__(
        self,
        surface: PlaywrightSurface,
        planner: LLMPlanner,
        safety: SafetyGuard,
        max_steps: int = 10,
    ):
        self.surface = surface
        self.planner = planner
        self.safety = safety
        self.max_steps = max_steps

        self.history: list[dict[str, Any]] = []
        self.outputs: dict[str, Any] = {}
        self.llm_calls = 0

    async def run(
        self,
        goal: str,
        target: str,
    ) -> dict[str, Any]:

        # Make sure the starting URL is allowed.
        self.safety.validate_url(target)

        # Open the target application.
        await self.surface.navigate(target)

        for step_number in range(
            1,
            self.max_steps + 1,
        ):

            # Observe the current UI.
            observation = await self.surface.observe()

            # Redact sensitive values before sending
            # anything to the LLM.
            safe_observation = redact_data(
                observation
            )

            # Ask the real LLM for exactly one next action.
            decision = self.planner.decide(
                goal=goal,
                observation=safe_observation,
                history=self.history,
            )

            self.llm_calls += 1

            print(
                f"\n--- DISCOVERY STEP "
                f"{step_number} ---"
            )

            print(
                "Action:",
                decision.action.action
            )

            print(
                "Reason:",
                decision.action.reason
            )

            # The model says the goal is complete.
            if (
                decision.goal_satisfied
                or decision.action.action == "finish"
            ):
                return {
                    "status": "success",
                    "goal": goal,
                    "outputs": self.outputs,
                    "history": self.history,
                    "llm_calls": self.llm_calls,
                }

            # The model cannot safely continue.
            if decision.action.action == "escalate":
                return {
                    "status": "escalation_required",
                    "goal": goal,
                    "reason": decision.action.reason,
                    "history": self.history,
                    "llm_calls": self.llm_calls,
                }

            # Check that the requested action is permitted.
            try:
                self.safety.validate_action(
                    decision.action.action
                )

            except SafetyViolation as exc:
                return {
                    "status": "safety_blocked",
                    "goal": goal,
                    "reason": str(exc),
                    "history": self.history,
                    "llm_calls": self.llm_calls,
                }

            # Execute the model's chosen action.
            await self._execute_action(
                decision.action
            )

            # Convert typed target model into a normal dict
            # before storing it in history.
            target_dict = None

            if decision.action.target:
                target_dict = (
                    decision.action.target.model_dump(
                        exclude_none=True
                    )
                )

            # Never persist typed values raw in history.
            history_entry = {
                "step": step_number,
                "action": (
                    decision.action.action
                ),
                "target": target_dict,
                "value": (
                    "[REDACTED]"
                    if decision.action.action == "type"
                    else decision.action.value
                ),
                "reason": (
                    decision.action.reason
                ),
            }

            self.history.append(
                history_entry
            )

        return {
            "status": "max_steps_reached",
            "goal": goal,
            "outputs": self.outputs,
            "history": self.history,
            "llm_calls": self.llm_calls,
        }

    async def _execute_action(
        self,
        action,
    ) -> None:

        if action.action == "type":

            if not action.target:
                raise ValueError(
                    "Type action requires a target."
                )

            if action.value is None:
                raise ValueError(
                    "Type action requires a value."
                )

            target_dict = (
                action.target.model_dump(
                    exclude_none=True
                )
            )

            await self.surface.type_text(
                target_dict,
                action.value,
            )

        elif action.action == "click":

            if not action.target:
                raise ValueError(
                    "Click action requires a target."
                )

            target_dict = (
                action.target.model_dump(
                    exclude_none=True
                )
            )

            await self.surface.click(
                target_dict
            )

            await self.surface.page.wait_for_load_state(
                "domcontentloaded"
            )

        elif action.action == "wait":

            await self.surface.page.wait_for_timeout(
                1000
            )

        elif action.action == "extract":

            value = await self._extract_value(
                action.target
            )

            output_name = (
                action.output_name
                or "extracted_value"
            )

            self.outputs[
                output_name
            ] = value

            print(
                f"Extracted "
                f"{output_name}: {value}"
            )

        else:
            raise ValueError(
                f"Unsupported discovery action: "
                f"{action.action}"
            )

    async def _extract_value(
        self,
        target,
    ) -> str:

        if not target:
            raise ValueError(
                "Extract action requires a target."
            )

        # AgentTarget is a Pydantic model.
        # Convert it into a regular dictionary.
        if hasattr(
            target,
            "model_dump"
        ):
            target = target.model_dump(
                exclude_none=True
            )

        strategy = target.get(
            "strategy"
        )

        if strategy == "text":

            label = (
                target.get("text")
                or target.get("name")
            )

            if not label:
                raise ValueError(
                    "Text extraction requires "
                    "text or name."
                )

            row = self.surface.page.locator(
                "tr",
                has_text=label,
            )

            if await row.count() == 0:
                raise ValueError(
                    f"Could not find row "
                    f"containing '{label}'"
                )

            cells = row.locator(
                "td"
            )

            if await cells.count() < 2:
                raise ValueError(
                    "Expected table row with "
                    "label and value."
                )

            value = (
                await cells.nth(
                    1
                ).inner_text()
            ).strip()

            return value

        raise ValueError(
            f"Unsupported extraction "
            f"strategy: {strategy}"
        )