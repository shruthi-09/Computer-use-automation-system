import os

from dotenv import load_dotenv
from openai import OpenAI

from src.agent.models import DiscoveryDecision
from src.agent.prompts import (
    DISCOVERY_SYSTEM_PROMPT,
    build_discovery_prompt,
)


load_dotenv()


class LLMPlanner:

    def __init__(
        self,
        model: str | None = None,
    ):
        api_key = os.getenv(
            "OPENROUTER_API_KEY"
        )

        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY is not set."
            )

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            timeout=60.0,
            max_retries=2,
        )

        self.model = (
            model
            or os.getenv(
                "OPENROUTER_MODEL",
                "openrouter/free",
            )
        )

    def decide(
        self,
        goal: str,
        observation: dict,
        history: list[dict],
    ) -> DiscoveryDecision:

        user_prompt = build_discovery_prompt(
            goal=goal,
            observation=observation,
            history=history,
        )

        system_prompt = (
            DISCOVERY_SYSTEM_PROMPT
            + """

IMPORTANT RULES:

Choose exactly one next UI action.

Only use these target strategies:

- role
- label
- text
- css
- placeholder

Never use "name" as a strategy.

Examples:

Member ID input:
{
  "strategy": "label",
  "label": "Member ID"
}

Search button:
{
  "strategy": "role",
  "role": "button",
  "name": "Search"
}

Savings balance extraction:
{
  "strategy": "text",
  "text": "Savings Balance"
}

If the requested value has not yet been extracted,
do not finish.

For this goal, extraction must happen before finish.
"""
        )

        schema = (
            DiscoveryDecision
            .model_json_schema()
        )

        response = (
            self.client
            .chat
            .completions
            .create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "discovery_decision",
                        "strict": True,
                        "schema": schema,
                    },
                },
                extra_body={
                    "provider": {
                        "require_parameters": True
                    }
                },
                temperature=0,
                max_tokens=500,
            )
        )

        content = (
            response
            .choices[0]
            .message
            .content
        )

        if not content:
            raise ValueError(
                "Model returned an empty response."
            )

        return (
            DiscoveryDecision
            .model_validate_json(
                content
            )
        )