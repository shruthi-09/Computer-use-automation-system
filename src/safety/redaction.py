from typing import Any


REDACTED = "[REDACTED]"

SENSITIVE_KEYS = {
    "member_id",
    "password",
    "passwd",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "api_key",
    "authorization",
    "ssn",
    "account_number",
    "routing_number",
}


def is_sensitive_key(key: str) -> bool:
    normalized = key.lower().strip()

    return (
        normalized in SENSITIVE_KEYS
        or normalized.endswith("_token")
        or normalized.endswith("_secret")
        or normalized.endswith("_password")
        or normalized.endswith("_key")
    )


def redact_value(
    key: str,
    value: Any,
) -> Any:

    if is_sensitive_key(key):
        return REDACTED

    return redact_data(value)


def redact_data(
    data: Any,
) -> Any:

    if isinstance(data, dict):
        return {
            key: redact_value(
                str(key),
                value,
            )
            for key, value in data.items()
        }

    if isinstance(data, list):
        return [
            redact_data(item)
            for item in data
        ]

    if isinstance(data, tuple):
        return tuple(
            redact_data(item)
            for item in data
        )

    return data
