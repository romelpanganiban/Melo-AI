from services.settings_service import SettingsService
from services.chat_service import ChatService


def test_get_settings():

    service = SettingsService()

    settings = service.get_settings()

    assert "model" in settings
    assert "provider" in settings
    assert "temperature" in settings
    assert "project_context" in settings
    assert isinstance(settings["project_context"], dict)
    assert "roadmap_summary" in settings["project_context"]


def test_chat_service_injects_project_context_into_prompt():
    service = ChatService.__new__(ChatService)
    service.learning_level = "intermediate"
    service.explanation_style = "clear"
    service.quiz_difficulty = "medium"
    service.project_context = {
        "project_name": "Melo roadmap",
        "roadmap_summary": "Keep the roadmap active until the user changes the goal.",
        "current_phase": "Context persistence",
        "current_objective": "Keep the project context active across requests.",
        "next_action": "Continue on the roadmap unless overridden.",
    }

    prompt = service._build_prompt(
        [{"role": "user", "content": "What is next on the roadmap?"}],
        "",
        "chat",
    )

    assert "Project context:" in prompt
    assert "Melo roadmap" in prompt
    assert "Default rule: stay on the current roadmap unless the user explicitly changes direction." in prompt
    assert "What is next on the roadmap?" in prompt