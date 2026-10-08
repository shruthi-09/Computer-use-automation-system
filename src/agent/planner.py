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
            timeout=45.0,
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
Do not use ```json fences.
Do not include explanations outside the JSON.

Every field must exist.

The JSON structure must be:

{
  "goal_satisfied": false,
  "action": {
    "action": "type",
    "target": {
      "strategy": "label",
      "role": null,
      "name": null,
      "label": "Member ID",
      "text": null,
      "selector": null,
      "placeholder": null
    },
    "value": "12345",
    "output_name": null,
    "reason": "Enter the requested member ID.",
    "confidence": 0.95
  },
  "summary": null
}

For extraction, use:

{
  "goal_satisfied": false,
  "action": {
    "action": "extract",
    "target": {
      "strategy": "text",
      "role": null,
      "name": null,
      "label": null,
      "text": "Savings Balance",
      "selector": null,
      "placeholder": null
    },
    "value": null,
    "output_name": "savings_balance",
    "reason": "Read the requested savings balance.",
    "confidence": 0.95
  },
  "summary": null
}

When the requested value has already been extracted, use:

{
  "goal_satisfied": true,
  "action": {
    "action": "finish",
    "target": null,
    "value": null,
    "output_name": null,
    "reason": "The requested result has been obtained.",
    "confidence": 1.0
  },
  "summary": "Goal completed."
}

Use null for fields that do not apply.
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
                        temperature=0,
                        max_tokens=700,
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