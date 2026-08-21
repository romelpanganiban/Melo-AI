from pathlib import Path

import pytest

from core.errors import ValidationError
from services.dataset_service import DatasetService


def test_create_dataset_writes_jsonl(tmp_path: Path):
    result = DatasetService(tmp_path).create_dataset(
        "support conversations",
        [{"messages": [
            {"role": "user", "content": "  Hello  "},
            {"role": "assistant", "content": "Hi there"},
        ]}],
    )

    assert result["name"] == "support-conversations"
    assert (tmp_path / "support-conversations.jsonl").read_text(encoding="utf-8") == '{"messages": [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi there"}]}\n'


def test_dataset_requires_user_and_assistant(tmp_path: Path):
    with pytest.raises(ValidationError):
        DatasetService(tmp_path).create_dataset(
            "invalid",
            [{"messages": [{"role": "user", "content": "Only one side"}]}],
        )


def test_dataset_rejects_invalid_role(tmp_path: Path):
    with pytest.raises(ValidationError):
        DatasetService(tmp_path).create_dataset(
            "invalid",
            [{"messages": [
                {"role": "user", "content": "Hello"},
                {"role": "bot", "content": "Hi"},
            ]}],
        )