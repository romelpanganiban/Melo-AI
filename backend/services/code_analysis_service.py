"""Read-only source file analysis for the coding assistant."""

from __future__ import annotations

import ast
import os
import re
import tempfile
from pathlib import Path

from core.errors import ChatServiceError, ValidationError
from core.settings import settings
from core.workspace_fs import WorkspaceFilesystem


class CodeAnalysisService:
    """Analyze source files inside the Melo-AI workspace without modifying them."""

    MAX_FILE_SIZE = 1_000_000
    SENSITIVE_FILENAMES = {".env", ".env.local", ".env.production", "id_rsa"}
    SENSITIVE_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}
    SUPPORTED_EXTENSIONS = {
        ".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".md", ".css", ".html"
    }

    def __init__(self, workspace_id: str | None = None):
        self.workspace_id = workspace_id
        self.workspace_root = self._workspace_root(workspace_id)

    def with_workspace(self, workspace_id: str | None) -> "CodeAnalysisService":
        return CodeAnalysisService(workspace_id=workspace_id)

    def analyze_file(self, relative_path: str, workspace_id: str | None = None) -> dict:
        requested = self._resolve_file(relative_path, workspace_id)
        content = self._read_text(requested)
        workspace = self._workspace_root(workspace_id or self.workspace_id)

        analysis = {
            "path": requested.relative_to(workspace).as_posix(),
            "extension": requested.suffix.lower().lstrip("."),
            "language": self._language_for(requested.suffix.lower()),
            "size_bytes": requested.stat().st_size,
            "line_count": len(content.splitlines()),
            "imports": [],
            "functions": [],
            "classes": [],
        }

        if requested.suffix.lower() == ".py":
            self._analyze_python(content, analysis)
        else:
            analysis["imports"] = self._find_generic_imports(content)
            analysis["functions"] = re.findall(
                r"(?:function\s+|(?:async\s+)?def\s+)([A-Za-z_$][\w$]*)", content
            )
            analysis["classes"] = re.findall(
                r"\bclass\s+([A-Za-z_$][\w$]*)", content
            )

        return analysis

    def read_file(self, relative_path: str, workspace_id: str | None = None) -> dict:
        """Read a supported workspace file without modifying it."""
        requested = self._resolve_file(relative_path, workspace_id)
        content = self._read_text(requested)
        workspace = self._workspace_root(workspace_id or self.workspace_id)
        return {
            "path": requested.relative_to(workspace).as_posix(),
            "size_bytes": requested.stat().st_size,
            "line_count": len(content.splitlines()),
            "content": content,
        }

    def write_file(self, relative_path: str, content: str, confirm: bool, workspace_id: str | None = None) -> dict:
        """Write a UTF-8 workspace file using an atomic replacement."""
        if not confirm:
            raise ValidationError("confirm must be true before writing a file", field="confirm")
        if not isinstance(content, str):
            raise ValidationError("content must be a string", field="content")
        if len(content.encode("utf-8")) > self.MAX_FILE_SIZE:
            raise ValidationError("content exceeds the 1 MB write limit", field="content")

        workspace = self._workspace_root(workspace_id or self.workspace_id)
        if not relative_path or not relative_path.strip():
            raise ValidationError("path is required", field="path")
        requested = self._resolve_write_target(relative_path, workspace_id)
        if requested.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValidationError("file type is not supported", field="path")
        if requested.name.startswith(".") or any(part in {".git", ".venv", "node_modules"} for part in requested.parts):
            raise ValidationError("protected paths cannot be modified", field="path")

        existed = requested.exists()
        requested.parent.mkdir(parents=True, exist_ok=True)
        temporary_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=requested.parent, delete=False
            ) as temporary:
                temporary.write(content)
                temporary.flush()
                os.fsync(temporary.fileno())
                temporary_path = temporary.name
            os.replace(temporary_path, requested)
        except OSError as exc:
            if temporary_path:
                try:
                    os.unlink(temporary_path)
                except OSError:
                    pass
            raise ChatServiceError("failed to write file") from exc

        return {
            "path": requested.relative_to(workspace).as_posix(),
            "size_bytes": requested.stat().st_size,
            "line_count": len(content.splitlines()),
            "created": not existed,
        }

    def delete_file(self, relative_path: str, confirm: bool, workspace_id: str | None = None) -> dict:
        """Delete one supported workspace file after explicit confirmation."""
        if not confirm:
            raise ValidationError("confirm must be true before deleting a file", field="confirm")

        requested = self._resolve_file(relative_path, workspace_id)
        if requested.name.startswith(".") or any(
            part in {".git", ".venv", "node_modules"} for part in requested.parts
        ):
            raise ValidationError("protected paths cannot be modified", field="path")

        try:
            requested.unlink()
        except OSError as exc:
            raise ChatServiceError("failed to delete file") from exc

        workspace = self._workspace_root(workspace_id or self.workspace_id)
        return {
            "path": requested.relative_to(workspace).as_posix(),
            "deleted": True,
        }

    def _resolve_file(self, relative_path: str, workspace_id: str | None = None) -> Path:
        if not relative_path or not relative_path.strip():
            raise ValidationError("path is required", field="path")

        workspace = self._workspace_root(workspace_id or self.workspace_id)
        requested = self._resolve_workspace_path(relative_path, workspace)
        if self._is_sensitive_path(requested):
            raise ValidationError("sensitive files cannot be accessed", field="path")
        if not requested.is_file():
            raise ValidationError("file was not found", field="path")
        if requested.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValidationError("file type is not supported", field="path")
        if requested.stat().st_size > self.MAX_FILE_SIZE:
            raise ValidationError("file exceeds the 1 MB analysis limit", field="path")
        return requested

    @classmethod
    def _is_sensitive_path(cls, requested: Path) -> bool:
        return requested.name.lower() in cls.SENSITIVE_FILENAMES or requested.suffix.lower() in cls.SENSITIVE_SUFFIXES

    def _resolve_write_target(self, relative_path: str, workspace_id: str | None = None) -> Path:
        if not relative_path or not relative_path.strip():
            raise ValidationError("path is required", field="path")

        workspace = self._workspace_root(workspace_id or self.workspace_id)
        requested = self._resolve_workspace_path(relative_path, workspace)
        if requested.exists() and requested.is_dir():
            raise ValidationError("path must point to a file", field="path")
        return requested

    @staticmethod
    def _workspace_root(workspace_id: str | None) -> Path:
        base_root = Path(settings.BASE_DIR).resolve()
        if workspace_id and settings.WORKSPACE_TOOLS_ROOT:
            return Path(settings.WORKSPACE_TOOLS_ROOT).expanduser().resolve()
        if workspace_id:
            return (base_root / "workspaces" / workspace_id).resolve()
        return base_root

    @staticmethod
    def _resolve_workspace_path(relative_path: str, workspace: Path) -> Path:
        requested = (workspace / relative_path).resolve()
        if requested != workspace and workspace not in requested.parents:
            raise ValidationError("path must stay inside the workspace", field="path")
        return requested

    @staticmethod
    def _read_text(requested: Path) -> str:
        try:
            return requested.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ValidationError("file must be UTF-8 text", field="path") from exc
        except OSError as exc:
            raise ChatServiceError("failed to read file") from exc

    @staticmethod
    def _language_for(extension: str) -> str:
        return {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".json": "json",
            ".md": "markdown",
            ".css": "css",
            ".html": "html",
        }.get(extension, "text")

    @staticmethod
    def _analyze_python(content: str, analysis: dict) -> None:
        try:
            tree = ast.parse(content)
        except SyntaxError as exc:
            analysis["syntax_error"] = f"line {exc.lineno}: {exc.msg}"
            return

        analysis["imports"] = [
            node.names[0].name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import) and node.names
        ] + [
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        ]
        analysis["functions"] = [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        analysis["classes"] = [
            node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
        ]

    @staticmethod
    def _find_generic_imports(content: str) -> list[str]:
        imports = re.findall(r"^\s*import\s+([^;\n]+)", content, re.MULTILINE)
        imports += re.findall(r"^\s*from\s+([^\s]+)\s+import\s+", content, re.MULTILINE)
        return imports


_code_analysis_service = CodeAnalysisService()


def get_code_analysis_service() -> CodeAnalysisService:
    return _code_analysis_service
