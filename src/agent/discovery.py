from typing import Any

from src.agent.planner import LLMPlanner
from src.observability.logger import RunLogger
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

        self.logger = RunLogger(
            run_id="discovery-001",
            mode="discovery",
            output_path=(
                "evidence/discovery/events.jsonl"
            ),
        )

    async def run(
        self,
        goal: str,
        target: str,
    ) -> dict[str, Any]:

        self.logger.log(
            "run_started",
            goal=goal,
            target=target,
        )

        self.safety.validate_url(
            target
        )

        await self.surface.navigate(
            target
        )

        for step_number in range(
            1,
            self.max_steps + 1,
        ):

            observation = (
                await self.surface.observe()
            )

            safe_observation = redact_data(
                observation
            )

            self.logger.log(
                "observation_captured",
                step=step_number,
                title=observation.get(
                    "title"
                ),
                url=observation.get(
                    "url"
                ),
                control_count=len(
                    observation.get(
                        "controls",
                        [],
                    )
                ),
            )

            decision = self.planner.decide(
                goal=goal,
                observation=safe_observation,
                history=self.history,
            )

            self.llm_calls += 1

            target_dict = None

            if decision.action.target:
                target_dict = (
                    decision.action.target
                    .model_dump(
                        exclude_none=True
                    )
                )

            self.logger.log(
                "llm_decision",
                step=step_number,
                action=(
                    decision.action.action
                ),
                target=target_dict,
                reason=(
                    decision.action.reason
                ),
                confidence=(
                    decision.action.confidence
                ),
                llm_calls=self.llm_calls,
            )

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

            # If the model explicitly says the goal
            # is finished before another action,
            # stop successfully.
            if (
                decision.goal_satisfied
                or decision.action.action
                == "finish"
            ):

                self.logger.log(
                    "run_completed",
                    status="success",
                    reason=(
                        "model_declared_complete"
                    ),
                    llm_calls=self.llm_calls,
                    output_names=list(
                        self.outputs.keys()
                    ),
                )

                return {
                    "status": "success",
                    "goal": goal,
                    "outputs": self.outputs,
                    "history": self.history,
                    "llm_calls": self.llm_calls,
                }

            # Escalation requested by the model.
            if (
                decision.action.action
                == "escalate"
            ):

                self.logger.log(
                    "escalation_requested",
                    step=step_number,
                    reason=(
                        decision.action.reason
                    ),
                )

                return {
                    "status": (
                        "escalation_required"
                    ),
                    "goal": goal,
                    "reason": (
                        decision.action.reason
                    ),
                    "history": self.history,
                    "llm_calls": self.llm_calls,
                }

            # Deterministic safety policy decides
            # whether the proposed action is allowed.
            try:
                self.safety.validate_action(
                    decision.action.action
                )

            except SafetyViolation as exc:

                self.logger.log(
                    "safety_blocked",
                    step=step_number,
                    reason=str(exc),
                )

                return {
                    "status": "safety_blocked",
                    "goal": goal,
                    "reason": str(exc),
                    "history": self.history,
                    "llm_calls": self.llm_calls,
                }

            # Execute exactly one approved action.
            await self._execute_action(
                decision.action
            )

            history_entry = {
                "step": step_number,
                "action": (
                    decision.action.action
                ),
                "target": target_dict,
                "value": (
                    "[REDACTED]"
                    if (
                        decision.action.action
                        == "type"
                    )
                    else decision.action.value
                ),
                "reason": (
                    decision.action.reason
                ),
            }

            self.history.append(
                history_entry
            )

            self.logger.log(
                "action_executed",
                step=step_number,
                action=(
                    decision.action.action
                ),
                target=target_dict,
                value=(
                    "[REDACTED]"
                    if (
                        decision.action.action
                        == "type"
                    )
                    else None
                ),
            )

            # Deterministic stopping condition.
            #
            # For this capability, once the requested
            # value has been successfully extracted,
            # discovery is complete. We do not need
            # another LLM call just to say "finish".
            if (
                decision.action.action
                == "extract"
                and self.outputs
            ):

                self.logger.log(
                    "run_completed",
                    status="success",
                    reason=(
                        "required_output_extracted"
                    ),
                    llm_calls=self.llm_calls,
                    output_names=list(
                        self.outputs.keys()
                    ),
                )

                return {
                    "status": "success",
                    "goal": goal,
                    "outputs": self.outputs,
                    "history": self.history,
                    "llm_calls": self.llm_calls,
                }

        self.logger.log(
            "run_completed",
            status="max_steps_reached",
            llm_calls=self.llm_calls,
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
                    "Type action requires "
                    "a target."
                )

            if action.value is None:
                raise ValueError(
                    "Type action requires "
                    "a value."
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
                    "Click action requires "
                    "a target."
                )

            target_dict = (
                action.target.model_dump(
                    exclude_none=True
                )
            )

            await self.surface.click(
                target_dict
            )

            await (
                self.surface.page
                .wait_for_load_state(
                    "domcontentloaded"
                )
            )

        elif action.action == "wait":

            await (
                self.surface.page
                .wait_for_timeout(
                    1000
                )
            )

        elif action.action == "extract":

            value = (
                await self._extract_value(
                    action.target
                )
            )

            output_name = (
                action.output_name
                or "savings_balance"
            )

            self.outputs[
                output_name
            ] = value

            self.logger.log(
                "output_extracted",
                output_name=output_name,
            )

            print(
                f"Extracted "
                f"{output_name}: {value}"
            )

        else:
            raise ValueError(
                f"Unsupported discovery "
                f"action: {action.action}"
            )

    async def _extract_value(
        self,
        target,
    ) -> str:

        if not target:
            raise ValueError(
                "Extract action requires "
                "a target."
            )

        if hasattr(
            target,
            "model_dump",
        ):
            target = (
                target.model_dump(
                    exclude_none=True
                )
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

            row = (
                self.surface.page.locator(
                    "tr",
                    has_text=label,
                )
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
                    "Expected table row "
                    "with label and value."
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