from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from core.errors import ValidationError
from services.git_service import GitService


def test_status_parses_branch_and_changed_files(tmp_path: Path):
    result = Mock(returncode=0, stdout="## main...origin/main\n M app.py\n?? notes.md\n", stderr="")

    with patch("services.git_service.subprocess.run", return_value=result):
        status = GitService(tmp_path).status()

    assert status == {
        "branch": "main...origin/main",
        "files": [
            {"status": " M", "path": "app.py"},
            {"status": "??", "path": "notes.md"},
        ],
        "count": 2,
    }


def test_diff_rejects_path_outside_workspace(tmp_path: Path):
    with pytest.raises(ValidationError):
        GitService(tmp_path).diff("../outside.py")


def test_diff_passes_workspace_relative_path(tmp_path: Path):
    result = Mock(returncode=0, stdout="diff -- app.py\n", stderr="")

    with patch("services.git_service.subprocess.run", return_value=result) as run:
        response = GitService(tmp_path).diff("app.py")

    assert response == {"path": "app.py", "diff": "diff -- app.py\n"}
    assert run.call_args.args[0][-2:] == ["--", "app.py"]