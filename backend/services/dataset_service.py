"""Local dataset preparation for instruction fine-tuning."""

from __future__ import annotations

import json
import re
from pathlib import Path

from core.errors import ValidationError
from core.settings import settings


class DatasetService:
    """Validate and persist chat datasets as JSONL files."""

    MAX_EXAMPLES = 10_000
    MAX_CONTENT_LENGTH = 50_000

    def __init__(self, directory: Path | None = None):
        self.directory = directory or settings.TRAINING_DATA_DIR
        self.directory.mkdir(parents=True, exist_ok=True)

    def create_dataset(self, name: str, examples: list[dict]) -> dict:
        safe_name = self._safe_name(name)
        normalized = [self._normalize_example(example, index) for index, example in enumerate(examples)]
        path = self.directory / f"{safe_name}.jsonl"
        with path.open("w", encoding="utf-8", newline="\n") as dataset_file:
            for example in normalized:
                dataset_file.write(json.dumps(example, ensure_ascii=False) + "\n")
        return {
            "name": safe_name,
            "path": path.relative_to(settings.BASE_DIR).as_posix(),
            "example_count": len(normalized),
        }

    def list_datasets(self) -> list[dict]:
        return [
            {
                "name": path.stem,
                "path": path.relative_to(settings.BASE_DIR).as_posix(),
                "size_bytes": path.stat().st_size,
            }
            for path in sorted(self.directory.glob("*.jsonl"))
        ]

    def _normalize_example(self, example: dict, index: int) -> dict:
        if len(example.get("messages", [])) < 2:
            raise ValidationError(f"example {index + 1} needs user and assistant messages", field="examples")
        messages = example.get("messages")
        if not isinstance(messages, list):
            raise ValidationError(f"example {index + 1} messages must be a list", field="examples")

        normalized_messages = []
        for message in messages:
            if not isinstance(message, dict) or message.get("role") not in {"user", "assistant", "system"}:
                raise ValidationError(f"example {index + 1} has an invalid message role", field="examples")
            content = message.get("content")
            if not isinstance(content, str) or not content.strip():
                raise ValidationError(f"example {index + 1} has empty message content", field="examples")
            if len(content) > self.MAX_CONTENT_LENGTH:
                raise ValidationError(f"example {index + 1} message is too long", field="examples")
            normalized_messages.append({"role": message["role"], "content": content.strip()})

        roles = [message["role"] for message in normalized_messages]
        if "user" not in roles or "assistant" not in roles:
            raise ValidationError(f"example {index + 1} needs user and assistant messages", field="examples")
        return {"messages": normalized_messages}

    @staticmethod
    def _safe_name(name: str) -> str:
        safe_name = re.sub(r"[^a-zA-Z0-9_-]+", "-", name.strip()).strip("-")
        if not safe_name:
            raise ValidationError("dataset name is required", field="name")
        return safe_name[:100]