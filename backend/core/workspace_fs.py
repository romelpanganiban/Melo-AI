from __future__ import annotations

from pathlib import Path


class WorkspaceFilesystem:
    """Sandbox file access to a single workspace root."""

    def __init__(self, workspace_id: str, base_root: str | Path = "./workspaces"):
        self.workspace_id = workspace_id
        self.base_root = Path(base_root).resolve()
        self.root = (self.base_root / workspace_id).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def resolve_safe_path(self, relative_path: str) -> Path:
        if not relative_path or not relative_path.strip():
            raise ValueError("path cannot be empty")

        candidate = (self.root / relative_path).resolve()
        if candidate == self.root or self.root in candidate.parents:
            return candidate

        raise ValueError(f"Path traversal detected: {relative_path}")

    def read_file(self, relative_path: str) -> str | None:
        safe_path = self.resolve_safe_path(relative_path)
        if not safe_path.is_file():
            return None

        try:
            return safe_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return safe_path.read_bytes().decode("utf-8", errors="replace")

    def write_file(self, relative_path: str, content: str) -> Path:
        safe_path = self.resolve_safe_path(relative_path)
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        safe_path.write_text(content, encoding="utf-8")
        return safe_path

    def delete_file(self, relative_path: str) -> None:
        safe_path = self.resolve_safe_path(relative_path)
        safe_path.unlink()

    def path_for(self, relative_path: str) -> Path:
        return self.resolve_safe_path(relative_path)
