from typing import Any

from src.artifacts.models import (
    BusinessOutcome,
    CapabilityArtifact,
    ConditionSpec,
    HardFailure,
    InputParameter,
    OutputParameter,
    StepSpec,
    TargetSpec,
)


class ArtifactRecorder:

    def build_from_discovery(
        self,
        discovery_result: dict[str, Any],
    ) -> CapabilityArtifact:

        history = discovery_result.get(
            "history",
            []
        )

        steps: list[StepSpec] = []

        previous_signature = None

        for item in history:

            action = item.get("action")
            target_data = item.get("target")

            if not target_data:
                continue

            # Prevent repeated identical extraction
            # actions from becoming duplicate replay steps.
            signature = (
                action,
                str(target_data),
            )

            if (
                action == "extract"
                and signature == previous_signature
            ):
                continue

            previous_signature = signature

            target = TargetSpec(
                **target_data
            )

            step_id = (
                f"step_{len(steps) + 1}"
            )

            if action == "type":

                steps.append(
                    StepSpec(
                        id=step_id,
                        action="type",
                        target=target,
                        value="{{member_id}}",
                        description=(
                            "Enter the supplied "
                            "member ID."
                        ),
                    )
                )

            elif action == "click":

                steps.append(
                    StepSpec(
                        id=step_id,
                        action="click",
                        target=target,
                        description=(
                            "Submit the member search."
                        ),
                    )
                )

            elif action == "extract":

                steps.append(
                    StepSpec(
                        id=step_id,
                        action="extract",
                        target=target,
                        output="savings_balance",
                        description=(
                            "Extract the member "
                            "savings balance."
                        ),
                    )
                )

            elif action == "wait":

                steps.append(
                    StepSpec(
                        id=step_id,
                        action="wait",
                        target=target,
                        description=(
                            "Wait for the application "
                            "to finish loading."
                        ),
                    )
                )

        artifact = CapabilityArtifact(
            schema_version="1.0",

            capability_name=(
                "lookup_savings_balance"
            ),

            description=(
                "Look up a credit union member "
                "and return their current "
                "savings balance."
            ),

            target_application=(
                "community_credit_union"
            ),

            entry_point=(
                "http://127.0.0.1:8000"
            ),

            inputs={
                "member_id": InputParameter(
                    type="string",
                    required=True,
                    sensitive=True,
                    description=(
                        "Credit union member "
                        "identifier."
                    ),
                )
            },

            outputs={
                "savings_balance": OutputParameter(
                    type="string",
                    description=(
                        "Current savings "
                        "account balance."
                    ),
                )
            },

            steps=steps,

            checkpoint=ConditionSpec(
                type="visible_text",
                value="Member Details",
            ),

            business_outcomes=[
                BusinessOutcome(
                    code="MEMBER_NOT_FOUND",
                    description=(
                        "No member exists for "
                        "the supplied ID."
                    ),
                    condition=ConditionSpec(
                        type="visible_text",
                        value="Member Not Found",
                    ),
                )
            ],

            hard_failures=[
                HardFailure(
                    code="PERMISSION_DENIED",
                    description=(
                        "The operator does not "
                        "have permission to view "
                        "the requested member."
                    ),
                    condition=ConditionSpec(
                        type="visible_text",
                        value="Permission Denied",
                    ),
                )
            ],
        )

        return artifact