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


def test_stage_requires_confirmation(tmp_path: Path):
    with pytest.raises(ValidationError):
        GitService(tmp_path).stage(["app.py"], confirm=False)


def test_commit_requires_message_and_confirmation(tmp_path: Path):
    service = GitService(tmp_path)

    with pytest.raises(ValidationError):
        service.commit("", confirm=True)
    with pytest.raises(ValidationError):
        service.commit("Initial commit", confirm=False)


def test_stage_and_commit_run_expected_commands(tmp_path: Path):
    stage_result = Mock(returncode=0, stdout="", stderr="")
    staged_files_result = Mock(returncode=0, stdout="", stderr="")
    commit_result = Mock(returncode=0, stdout="[main abc123] Initial commit\n", stderr="")

    with patch(
        "services.git_service.subprocess.run",
        side_effect=[stage_result, staged_files_result, commit_result],
    ) as run:
        staged = GitService(tmp_path).stage(["app.py"], confirm=True)
        committed = GitService(tmp_path).commit("Initial commit", confirm=True)

    assert staged == {"staged": ["app.py"], "count": 1}
    assert committed["message"] == "Initial commit"
    assert run.call_args_list[0].args[0][-3:] == ["add", "--", "app.py"]
    assert run.call_args_list[1].args[0][-5:] == ["diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR"]
    assert run.call_args_list[2].args[0][-3:] == ["commit", "-m", "Initial commit"]


def test_stage_blocks_sensitive_paths(tmp_path: Path):
    with pytest.raises(ValidationError, match="sensitive files"):
        GitService(tmp_path).stage([".env"], confirm=True)


def test_commit_blocks_sensitive_staged_files(tmp_path: Path):
    result = Mock(returncode=0, stdout=".env\0notes.md\0", stderr="")

    with patch("services.git_service.subprocess.run", return_value=result) as run:
        with pytest.raises(ValidationError, match="sensitive files"):
            GitService(tmp_path).commit("Initial commit", confirm=True)

    assert run.call_args.args[0][-5:] == ["diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR"]