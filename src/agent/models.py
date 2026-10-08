from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AgentTarget(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    strategy: Literal[
        "role",
        "label",
        "text",
        "css",
        "placeholder",
    ]

    role: str | None = None
    name: str | None = None
    label: str | None = None
    text: str | None = None
    selector: str | None = None
    placeholder: str | None = None


class AgentAction(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    action: Literal[
        "click",
        "type",
        "extract",
        "wait",
        "finish",
        "escalate",
    ]

    target: AgentTarget | None = None
    value: str | None = None
    output_name: str | None = None
    reason: str

    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
    )


class DiscoveryDecision(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    goal_satisfied: bool = False
    action: AgentAction
    summary: str | None = None