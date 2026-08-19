"""Read-only source file analysis for the coding assistant."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from core.errors import ChatServiceError, ValidationError
from core.settings import settings


class CodeAnalysisService:
    """Analyze source files inside the Melo-AI workspace without modifying them."""

    MAX_FILE_SIZE = 1_000_000
    SUPPORTED_EXTENSIONS = {
        ".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".md", ".css", ".html"
    }

    def analyze_file(self, relative_path: str) -> dict:
        if not relative_path or not relative_path.strip():
            raise ValidationError("path is required", field="path")

        workspace = Path(settings.BASE_DIR).resolve()
        requested = (workspace / relative_path).resolve()
        if requested != workspace and workspace not in requested.parents:
            raise ValidationError("path must stay inside the workspace", field="path")
        if not requested.is_file():
            raise ValidationError("file was not found", field="path")
        if requested.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValidationError("file type is not supported", field="path")
        if requested.stat().st_size > self.MAX_FILE_SIZE:
            raise ValidationError("file exceeds the 1 MB analysis limit", field="path")

        try:
            content = requested.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ValidationError("file must be UTF-8 text", field="path") from exc
        except OSError as exc:
            raise ChatServiceError("failed to read file") from exc

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
