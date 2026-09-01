"""Read-only Git status and diff access for the workspace."""

from __future__ import annotations

import shutil
import subprocess  # nosec B404
from pathlib import Path

from core.errors import ChatServiceError, ValidationError
from core.settings import settings


class GitService:
    """Inspect the workspace repository without changing Git state."""

    COMMAND_TIMEOUT = 10

    def __init__(self, workspace: Path | None = None, workspace_id: str | None = None):
        if workspace is not None:
            self.workspace = workspace.resolve()
        elif workspace_id:
            self.workspace = (Path(settings.BASE_DIR).resolve() / "workspaces" / workspace_id).resolve()
        else:
            self.workspace = Path(settings.BASE_DIR).resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)

    def status(self) -> dict:
        output = self._run("status", "--short", "--branch")
        lines = output.splitlines()
        branch = ""
        files: list[dict[str, str]] = []

        if lines and lines[0].startswith("## "):
            branch = lines.pop(0)[3:]

        for line in lines:
            if len(line) < 4:
                continue
            files.append({"status": line[:2], "path": line[3:]})

        return {"branch": branch, "files": files, "count": len(files)}

    def diff(self, path: str | None = None) -> dict:
        command = ["diff", "--no-ext-diff", "--unified=3"]
        if path:
            command.extend(["--", self._validate_path(path)])
        return {"path": path, "diff": self._run(*command)}

    def stage(self, paths: list[str], confirm: bool) -> dict:
        if not confirm:
            raise ValidationError("confirm must be true before staging files", field="confirm")
        if not paths:
            raise ValidationError("at least one path is required", field="paths")

        validated_paths = [self._validate_path(path) for path in paths]
        self._run("add", "--", *validated_paths)
        return {"staged": validated_paths, "count": len(validated_paths)}

    def commit(self, message: str, confirm: bool) -> dict:
        if not confirm:
            raise ValidationError("confirm must be true before committing", field="confirm")
        if not message or not message.strip():
            raise ValidationError("commit message is required", field="message")

        output = self._run("commit", "-m", message.strip())
        return {"message": message.strip(), "output": output}

    def _validate_path(self, relative_path: str) -> str:
        if not relative_path.strip():
            raise ValidationError("path cannot be empty", field="path")
        workspace_path = (self.workspace / relative_path).resolve()
        if workspace_path != self.workspace and self.workspace not in workspace_path.parents:
            raise ValidationError("path must stay inside the workspace", field="path")
        return workspace_path.relative_to(self.workspace).as_posix()

    def _run(self, *arguments: str) -> str:
        git_executable = shutil.which("git")
        if not git_executable:
            raise ChatServiceError("Git is not installed or not available on PATH")

        try:
            result = subprocess.run(  # nosec B603
                [git_executable, "-C", str(self.workspace), *arguments],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.COMMAND_TIMEOUT,
                check=False,
                shell=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ChatServiceError("Git is unavailable or timed out") from exc

        if result.returncode != 0:
            message = result.stderr.strip() or "Git command failed"
            raise ChatServiceError(message)
        return result.stdout