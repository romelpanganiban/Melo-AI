from pathlib import Path

import pytest

from core.errors import ValidationError
from core.settings import settings
from core.workspace_fs import WorkspaceFilesystem
from services.code_analysis_service import CodeAnalysisService


def test_write_file_creates_and_overwrites_in_workspace(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "BASE_DIR", tmp_path)
    service = CodeAnalysisService()

    created = service.write_file("notes.py", "print('first')\n", confirm=True)
    updated = service.write_file("notes.py", "print('second')\n", confirm=True)

    assert created["created"] is True
    assert updated["created"] is False
    assert (tmp_path / "notes.py").read_text(encoding="utf-8") == "print('second')\n"


def test_write_file_requires_confirmation(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "BASE_DIR", tmp_path)

    with pytest.raises(ValidationError):
        CodeAnalysisService().write_file("notes.py", "content", confirm=False)

    assert not (tmp_path / "notes.py").exists()


def test_write_file_rejects_protected_and_escape_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "BASE_DIR", tmp_path)
    service = CodeAnalysisService()

    with pytest.raises(ValidationError):
        service.write_file("../outside.py", "content", confirm=True)
    with pytest.raises(ValidationError):
        service.write_file(".env", "secret", confirm=True)
    with pytest.raises(ValidationError):
        service.write_file(".git/config.py", "content", confirm=True)


def test_delete_file_requires_confirmation_and_removes_file(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "BASE_DIR", tmp_path)
    target = tmp_path / "delete-me.py"
    target.write_text("pass\n", encoding="utf-8")
    service = CodeAnalysisService()

    with pytest.raises(ValidationError):
        service.delete_file("delete-me.py", confirm=False)
    assert target.exists()

    result = service.delete_file("delete-me.py", confirm=True)

    assert result == {"path": "delete-me.py", "deleted": True}
    assert not target.exists()


def test_workspace_filesystem_isolates_workspaces(tmp_path):
    root = tmp_path / "workspaces"
    ws_a = WorkspaceFilesystem("workspace-a", base_root=root)
    ws_b = WorkspaceFilesystem("workspace-b", base_root=root)

    ws_a.write_file("notes.py", "print('A')\n")
    assert (root / "workspace-a" / "notes.py").read_text(encoding="utf-8") == "print('A')\n"

    with pytest.raises(ValueError):
        ws_a.resolve_safe_path("../workspace-b/secret.txt")

    with pytest.raises(ValueError):
        ws_b.resolve_safe_path("../../etc/passwd")

    assert ws_b.read_file("notes.py") is None
