"""AI-assisted code review and generation without chat-history side effects."""

from services.code_analysis_service import get_code_analysis_service
from services.ollama_client import OllamaClient
from core.errors import ValidationError
from core.settings import settings


class CodeAssistantService:
    """Generate coding guidance using the configured local model."""

    def __init__(self):
        self.files = get_code_analysis_service()
        self.ollama = OllamaClient(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            timeout=settings.OLLAMA_TIMEOUT,
        )

    def review_file(self, path: str, instruction: str | None = None) -> dict:
        file_data = self.files.read_file(path)
        request = instruction.strip() if instruction else "Review this file for bugs, risks, and concrete improvements."
        prompt = (
            "You are a careful senior code reviewer. Return concise findings with severity, "
            "reasoning, and suggested fixes. Do not modify the file.\n\n"
            f"User request: {request}\n\n"
            f"File: {file_data['path']}\n"
            f"```\n{file_data['content']}\n```"
        )
        return {
            "path": file_data["path"],
            "result": self._generate(prompt),
        }

    def generate_code(self, path: str, instruction: str) -> dict:
        if not instruction or not instruction.strip():
            raise ValidationError("instruction is required", field="instruction")

        file_data = self.files.read_file(path)
        prompt = (
            "You are a local coding assistant. Propose a complete replacement for the requested "
            "file content. Return only the code, without Markdown fences or commentary. Preserve "
            "existing behavior unless the request requires changing it.\n\n"
            f"Request: {instruction.strip()}\n\n"
            f"File: {file_data['path']}\n"
            f"Current content:\n{file_data['content']}"
        )
        return {
            "path": file_data["path"],
            "result": self._generate(prompt),
        }

    def _generate(self, prompt: str) -> str:
        return self.ollama.generate_response(
            prompt=prompt,
            system_prompt=settings.SYSTEM_PROMPT,
            temperature=settings.OLLAMA_TEMPERATURE,
            top_p=settings.OLLAMA_TOP_P,
            top_k=settings.OLLAMA_TOP_K,
        ).strip()