from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class InputParameter(BaseModel):
    type: Literal["string", "integer", "number", "boolean"]
    required: bool = True
    sensitive: bool = False
    description: str | None = None


class OutputParameter(BaseModel):
    type: Literal["string", "integer", "number", "boolean"]
    description: str | None = None


class TargetSpec(BaseModel):
    strategy: Literal[
        "role",
        "label",
        "text",
        "css",
        "placeholder"
    ]

    role: str | None = None
    name: str | None = None
    label: str | None = None
    text: str | None = None
    selector: str | None = None
    placeholder: str | None = None

    fallbacks: list["TargetSpec"] = Field(
        default_factory=list
    )


class StepSpec(BaseModel):
    id: str

    action: Literal[
        "navigate",
        "click",
        "type",
        "extract",
        "wait"
    ]

    target: TargetSpec | None = None

    value: str | None = None

    output: str | None = None

    timeout_ms: int = 5000

    description: str | None = None


class ConditionSpec(BaseModel):
    type: Literal[
        "visible_text",
        "url_contains",
        "element_visible"
    ]

    value: str | None = None

    target: TargetSpec | None = None


class BusinessOutcome(BaseModel):
    code: str
    description: str
    condition: ConditionSpec

class HardFailure(BaseModel):
    code: str
    description: str
    condition: ConditionSpec


class CapabilityArtifact(BaseModel):
    schema_version: str = "1.0"

    capability_name: str

    description: str

    target_application: str

    entry_point: str

    inputs: dict[str, InputParameter]

    outputs: dict[str, OutputParameter]

    steps: list[StepSpec]

    checkpoint: ConditionSpec

    business_outcomes: list[BusinessOutcome] = Field(
        default_factory=list
    )

    hard_failures: list[HardFailure] = Field(
    default_factory=list
)