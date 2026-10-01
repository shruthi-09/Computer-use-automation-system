from urllib.parse import urlparse

from pydantic import BaseModel, Field


class SafetyViolation(Exception):
    """Raised when an attempted action violates safety policy."""
    pass


class SafetyPolicy(BaseModel):
    allowed_hosts: set[str] = Field(
        default_factory=lambda: {
            "127.0.0.1",
            "localhost",
        }
    )

    allowed_routes: set[str] = Field(
        default_factory=lambda: {
            "/",
            "/member",
        }
    )

    allowed_actions: set[str] = Field(
        default_factory=lambda: {
            "navigate",
            "click",
            "type",
            "extract",
            "wait",
        }
    )

    risky_actions: set[str] = Field(
        default_factory=lambda: {
            "submit_irreversible",
            "transfer_funds",
            "delete_record",
        }
    )

    blocked_actions: set[str] = Field(
        default_factory=lambda: {
            "execute_script",
            "file_upload",
            "external_navigation",
        }
    )

    require_confirmation_for_risky: bool = True


class SafetyGuard:

    def __init__(
        self,
        policy: SafetyPolicy | None = None,
    ):
        self.policy = policy or SafetyPolicy()

    def validate_url(
        self,
        url: str,
    ) -> None:

        parsed = urlparse(url)

        host = parsed.hostname or ""
        path = parsed.path or "/"

        if host not in self.policy.allowed_hosts:
            raise SafetyViolation(
                f"Host is not allowlisted: {host}"
            )

        if path not in self.policy.allowed_routes:
            raise SafetyViolation(
                f"Route is not allowlisted: {path}"
            )

    def validate_action(
        self,
        action: str,
        confirmed: bool = False,
    ) -> None:

        if action in self.policy.blocked_actions:
            raise SafetyViolation(
                f"Action is explicitly blocked: {action}"
            )

        if action in self.policy.risky_actions:

            if (
                self.policy.require_confirmation_for_risky
                and not confirmed
            ):
                raise SafetyViolation(
                    f"Risky action requires human "
                    f"confirmation: {action}"
                )

            return

        if action not in self.policy.allowed_actions:
            raise SafetyViolation(
                f"Action is not allowlisted: {action}"
            )