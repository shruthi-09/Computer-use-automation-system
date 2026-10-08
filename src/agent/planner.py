import json
import os
import time

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
            max_retries=0,
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

IMPORTANT OUTPUT RULES:

Return ONLY one valid JSON object.

Do not use markdown.
Do not use code fences.
Do not include text before or after the JSON.

Use exactly these action values:

click
type
extract
wait
finish
escalate

Use only these target strategies:

role
label
text
css
placeholder

Never use "name" as a strategy.

Examples:

Member ID input:

{
  "goal_satisfied": false,
  "action": {
    "action": "type",
    "target": {
      "strategy": "label",
      "label": "Member ID"
    },
    "value": "12345",
    "output_name": null,
    "reason": "Enter the requested member ID.",
    "confidence": 0.95
  },
  "summary": null
}

Search button:

{
  "goal_satisfied": false,
  "action": {
    "action": "click",
    "target": {
      "strategy": "role",
      "role": "button",
      "name": "Search"
    },
    "value": null,
    "output_name": null,
    "reason": "Submit the member search.",
    "confidence": 0.95
  },
  "summary": null
}

Savings Balance extraction:

{
  "goal_satisfied": false,
  "action": {
    "action": "extract",
    "target": {
      "strategy": "text",
      "text": "Savings Balance"
    },
    "value": null,
    "output_name": "savings_balance",
    "reason": "Read the savings balance.",
    "confidence": 0.95
  },
  "summary": null
}

Do not finish until the requested value has been extracted.
"""
        )

        last_error = None

        for attempt in range(1, 4):

            try:
                print(
                    f"Planner attempt {attempt}/3..."
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
                            "type": "json_object"
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

                content = self._clean_json(
                    content
                )

                parsed = json.loads(
                    content
                )

                decision = (
                    DiscoveryDecision
                    .model_validate(
                        parsed
                    )
                )

                return decision

            except Exception as exc:
                last_error = exc

                print(
                    f"Planner attempt {attempt} "
                    f"failed: {exc}"
                )

                if attempt < 3:
                    print(
                        "Waiting before retry..."
                    )

                    time.sleep(
                        3 * attempt
                    )

        raise RuntimeError(
            "Planner failed after "
            f"3 attempts. Last error: "
            f"{last_error}"
        )

    @staticmethod
    def _clean_json(
        content: str,
    ) -> str:

        content = content.strip()

        if content.startswith("```json"):
            content = content[
                len("```json"):
            ].strip()

        elif content.startswith("```"):
            content = content[
                len("```"):
            ].strip()

        if content.endswith("```"):
            content = content[:-3].strip()

        first_brace = content.find("{")
        last_brace = content.rfind("}")

        if (
            first_brace == -1
            or last_brace == -1
        ):
            raise ValueError(
                "No JSON object found "
                "in model response."
            )

        return content[
            first_brace:
            last_brace + 1
        ]