from src.artifacts.models import (
    BusinessOutcome,
    CapabilityArtifact,
    ConditionSpec,
    InputParameter,
    OutputParameter,
    StepSpec,
    TargetSpec,
)

from src.artifacts.store import save_artifact, load_artifact


artifact = CapabilityArtifact(
    capability_name="lookup_savings_balance",
    description=(
        "Look up a credit union member and return "
        "their current savings balance."
    ),
    target_application="community_credit_union",
    entry_point="http://127.0.0.1:8000",
    inputs={
        "member_id": InputParameter(
            type="string",
            required=True,
            sensitive=True,
            description="Credit union member identifier",
        )
    },
    outputs={
        "savings_balance": OutputParameter(
            type="string",
            description="Current savings account balance",
        )
    },
    steps=[
        StepSpec(
            id="step_1",
            action="type",
            target=TargetSpec(
                strategy="label",
                label="Member ID",
            ),
            value="{{member_id}}",
            description="Enter the supplied member ID.",
        ),
        StepSpec(
            id="step_2",
            action="click",
            target=TargetSpec(
                strategy="role",
                role="button",
                name="Search",
            ),
            description="Submit the member search.",
        ),
        StepSpec(
            id="step_3",
            action="extract",
            target=TargetSpec(
                strategy="text",
                text="Savings Balance",
            ),
            output="savings_balance",
            description="Read the member savings balance.",
        ),
    ],
    checkpoint=ConditionSpec(
        type="visible_text",
        value="Member Details",
    ),
    business_outcomes=[
        BusinessOutcome(
            code="MEMBER_NOT_FOUND",
            description="No member exists for the supplied ID.",
            condition=ConditionSpec(
                type="visible_text",
                value="Member Not Found",
            ),
        )
    ],
)


print("\nARTIFACT CREATED SUCCESSFULLY\n")

print(
    artifact.model_dump_json(
        indent=2
    )
)

output_path = "artifacts/examples/lookup_savings_balance-v1.json"

save_artifact(
    artifact,
    output_path
)

print(f"\nArtifact saved to: {output_path}")

loaded_artifact = load_artifact(
    output_path
)

print("\nARTIFACT LOADED SUCCESSFULLY")

print(
    "Capability:",
    loaded_artifact.capability_name
)

print(
    "Schema version:",
    loaded_artifact.schema_version
)