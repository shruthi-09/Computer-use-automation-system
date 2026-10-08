import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.safety.redaction import redact_data


class RunLogger:

    def __init__(
        self,
        run_id: str,
        mode: str,
        output_path: str,
    ):
        self.run_id = run_id
        self.mode = mode
        self.output_path = Path(output_path)

        self.output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def log(
        self,
        event: str,
        **details: Any,
    ) -> None:

        record = {
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "run_id": self.run_id,
            "mode": self.mode,
            "event": event,
            **details,
        }

        safe_record = redact_data(
            record
        )

        with self.output_path.open(
            "a",
            encoding="utf-8",
        ) as file:
            file.write(
                json.dumps(
                    safe_record
                )
                + "\n"
            )