from pathlib import Path

import pytest

from core.errors import ValidationError
from services.code_analysis_service import CodeAnalysisService


def test_analyze_python_file():
    result = CodeAnalysisService().analyze_file("backend/services/code_analysis_service.py")

    assert result["language"] == "python"
    assert result["line_count"] > 1
    assert "CodeAnalysisService" in result["classes"]
    assert "analyze_file" in result["functions"]
    assert "ast" in result["imports"]


def test_analyze_typescript_file():
    result = CodeAnalysisService().analyze_file("frontend/lib/api.ts")

    assert result["language"] == "typescript"
    assert result["line_count"] > 1
    assert "sendMessage" in result["functions"]


@pytest.mark.parametrize("path", ["missing.py", "..\\outside.txt"])
def test_rejects_invalid_paths(path):
    with pytest.raises(ValidationError):
        CodeAnalysisService().analyze_file(path)
