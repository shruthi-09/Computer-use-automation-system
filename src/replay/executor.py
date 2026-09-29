from typing import Any

from src.artifacts.models import CapabilityArtifact, StepSpec
from src.replay.models import (
    ReplayError,
    ReplayResult,
    ReplayStatus,
)
from src.surface.playwright_surface import PlaywrightSurface


class ReplayExecutor:

    def __init__(
        self,
        surface: PlaywrightSurface,
    ):
        self.surface = surface

    async def run(
        self,
        artifact: CapabilityArtifact,
        inputs: dict[str, Any],
    ) -> ReplayResult:

        completed_steps: list[str] = []
        outputs: dict[str, Any] = {}

        try:
            await self.surface.navigate(
                artifact.entry_point
            )

            for step in artifact.steps:

                business_result = (
                    await self._check_business_outcomes(
                        artifact,
                        completed_steps,
                        outputs,
                    )
                )

                if business_result:
                    return business_result

                await self._execute_step(
                    step,
                    inputs,
                    outputs,
                )

                completed_steps.append(step.id)

            business_result = (
                await self._check_business_outcomes(
                    artifact,
                    completed_steps,
                    outputs,
                )
            )

            if business_result:
                return business_result

            checkpoint_ok = (
                await self._verify_checkpoint(
                    artifact
                )
            )

            if not checkpoint_ok:
                screenshot_path = (
                    "evidence/replay/"
                    "checkpoint-failure.png"
                )

                await self.surface.screenshot(
                    screenshot_path
                )

                return ReplayResult(
                    status=ReplayStatus.FAILURE,
                    capability_name=(
                        artifact.capability_name
                    ),
                    outputs=outputs,
                    completed_steps=completed_steps,
                    llm_calls=0,
                    error=ReplayError(
                        code="CHECKPOINT_FAILED",
                        message=(
                            "Replay completed steps "
                            "but final checkpoint "
                            "was not satisfied."
                        ),
                        expected=(
                            artifact.checkpoint.value
                        ),
                        screenshot=screenshot_path,
                    ),
                )

            return ReplayResult(
                status=ReplayStatus.SUCCESS,
                capability_name=(
                    artifact.capability_name
                ),
                outputs=outputs,
                completed_steps=completed_steps,
                llm_calls=0,
            )

        except Exception as exc:

            screenshot_path = (
                "evidence/replay/"
                "replay-failure.png"
            )

            try:
                await self.surface.screenshot(
                    screenshot_path
                )
            except Exception:
                screenshot_path = None

            return ReplayResult(
                status=ReplayStatus.FAILURE,
                capability_name=(
                    artifact.capability_name
                ),
                outputs=outputs,
                completed_steps=completed_steps,
                llm_calls=0,
                error=ReplayError(
                    code="REPLAY_EXECUTION_ERROR",
                    message=str(exc),
                    screenshot=screenshot_path,
                ),
            )

    async def _execute_step(
        self,
        step: StepSpec,
        inputs: dict[str, Any],
        outputs: dict[str, Any],
    ) -> None:

        if step.action == "type":

            value = self._resolve_value(
                step.value,
                inputs,
            )

            await self.surface.type_text(
                step.target.model_dump(),
                value,
            )

        elif step.action == "click":

            await self.surface.click(
                step.target.model_dump()
            )

            await self.surface.page.wait_for_load_state(
                "domcontentloaded"
            )

        elif step.action == "wait":

            await self.surface.page.wait_for_timeout(
                step.timeout_ms
            )

        elif step.action == "extract":

            extracted_value = (
                await self._extract_value(step)
            )

            if step.output:
                outputs[step.output] = (
                    extracted_value
                )

        elif step.action == "navigate":

            value = self._resolve_value(
                step.value,
                inputs,
            )

            await self.surface.navigate(value)

        else:
            raise ValueError(
                f"Unsupported replay action: "
                f"{step.action}"
            )

    async def _extract_value(
        self,
        step: StepSpec,
    ) -> str:

        target = step.target

        if (
            target.strategy == "text"
            and target.text
        ):
            row = self.surface.page.locator(
                "tr",
                has_text=target.text,
            )

            if await row.count() == 0:
                raise ValueError(
                    f"Could not find row containing "
                    f"'{target.text}'"
                )

            cells = row.locator("td")

            if await cells.count() < 2:
                raise ValueError(
                    "Expected a table row with "
                    "a label and value."
                )

            return (
                await cells.nth(1).inner_text()
            ).strip()

        raise ValueError(
            f"Unsupported extraction target: "
            f"{target.strategy}"
        )

    async def _verify_checkpoint(
        self,
        artifact: CapabilityArtifact,
    ) -> bool:

        condition = artifact.checkpoint

        if (
            condition.type
            == "visible_text"
            and condition.value
        ):
            locator = (
                self.surface.page.get_by_text(
                    condition.value,
                    exact=False,
                )
            )

            return await locator.count() > 0

        return False

    async def _check_business_outcomes(
        self,
        artifact: CapabilityArtifact,
        completed_steps: list[str],
        outputs: dict[str, Any],
    ) -> ReplayResult | None:

        for outcome in artifact.business_outcomes:

            condition = outcome.condition

            if (
                condition.type
                == "visible_text"
                and condition.value
            ):
                locator = (
                    self.surface.page.get_by_text(
                        condition.value,
                        exact=False,
                    )
                )

                if await locator.count() > 0:

                    return ReplayResult(
                        status=(
                            ReplayStatus.BUSINESS_OUTCOME
                        ),
                        capability_name=(
                            artifact.capability_name
                        ),
                        outputs=outputs,
                        business_outcome=(
                            outcome.code
                        ),
                        completed_steps=(
                            completed_steps
                        ),
                        llm_calls=0,
                    )

        return None

    def _resolve_value(
        self,
        value: str | None,
        inputs: dict[str, Any],
    ) -> str:

        if value is None:
            return ""

        if (
            value.startswith("{{")
            and value.endswith("}}")
        ):
            key = value[2:-2].strip()

            if key not in inputs:
                raise ValueError(
                    f"Missing required input: {key}"
                )

            return str(inputs[key])

        return value