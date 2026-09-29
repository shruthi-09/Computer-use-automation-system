from pathlib import Path

from src.artifacts.models import CapabilityArtifact


def save_artifact(
    artifact: CapabilityArtifact,
    output_path: str
) -> None:
    path = Path(output_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    path.write_text(
        artifact.model_dump_json(indent=2),
        encoding="utf-8"
    )


def load_artifact(
    input_path: str
) -> CapabilityArtifact:
    path = Path(input_path)

    content = path.read_text(
        encoding="utf-8"
    )

    return CapabilityArtifact.model_validate_json(
        content
    )