from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ReplayStatus(str, Enum):
    SUCCESS = "success"
    BUSINESS_OUTCOME = "business_outcome"
    RECOVERED = "recovered"
    FAILURE = "failure"


class ReplayError(BaseModel):
    code: str
    message: str

    step_id: str | None = None

    expected: str | None = None
    observed: str | None = None

    screenshot: str | None = None


class ReplayResult(BaseModel):
    status: ReplayStatus

    capability_name: str

    outputs: dict[str, Any] = Field(
        default_factory=dict
    )

    business_outcome: str | None = None

    error: ReplayError | None = None

    completed_steps: list[str] = Field(
        default_factory=list
    )

    llm_calls: int = 0