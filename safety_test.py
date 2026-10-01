from src.safety.policy import (
    SafetyGuard,
    SafetyViolation,
)

from src.safety.redaction import redact_data


def test_allowed_action():
    guard = SafetyGuard()

    guard.validate_action("click")

    print("PASS: Allowed action accepted.")


def test_blocked_action():
    guard = SafetyGuard()

    try:
        guard.validate_action(
            "execute_script"
        )

        print(
            "FAIL: Blocked action was allowed."
        )

    except SafetyViolation as exc:
        print(
            "PASS: Blocked action rejected."
        )
        print("Reason:", exc)


def test_risky_action():
    guard = SafetyGuard()

    try:
        guard.validate_action(
            "transfer_funds"
        )

        print(
            "FAIL: Risky action did not "
            "require confirmation."
        )

    except SafetyViolation as exc:
        print(
            "PASS: Risky action requires "
            "confirmation."
        )
        print("Reason:", exc)


def test_risky_action_with_confirmation():
    guard = SafetyGuard()

    guard.validate_action(
        "transfer_funds",
        confirmed=True,
    )

    print(
        "PASS: Confirmed risky action accepted."
    )


def test_url_allowlist():
    guard = SafetyGuard()

    guard.validate_url(
        "http://127.0.0.1:8000/member"
    )

    print(
        "PASS: Allowlisted URL accepted."
    )


def test_redaction():

    original = {
        "member_id": "12345",
        "action": "member_search",
        "api_key": "super-secret-key",
        "nested": {
            "password": "mypassword",
            "status": "success",
        },
    }

    redacted = redact_data(
        original
    )

    print("\nRedacted data:")
    print(redacted)

    assert (
        redacted["member_id"]
        == "[REDACTED]"
    )

    assert (
        redacted["api_key"]
        == "[REDACTED]"
    )

    assert (
        redacted["nested"]["password"]
        == "[REDACTED]"
    )

    assert (
        redacted["action"]
        == "member_search"
    )

    print(
        "PASS: Sensitive data redacted."
    )


if __name__ == "__main__":

    print("\n--- SAFETY TESTS ---\n")

    test_allowed_action()

    test_blocked_action()

    test_risky_action()

    test_risky_action_with_confirmation()

    test_url_allowlist()

    test_redaction()

    print(
        "\nSUCCESS: All safety tests passed."
    )