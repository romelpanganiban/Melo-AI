from services.chat_service import ChatService


def test_ask_prompt_requires_grounded_filename_citations():
    service = object.__new__(ChatService)
    prompt = service._build_prompt(
        [{"role": "user", "content": "What does the guide say?"}],
        "[guide.pdf]\nUse staged approvals.",
        "ask",
    )

    assert "using only the provided document context" in prompt
    assert "do not guess" in prompt
    assert "[guide.pdf]" in prompt
    assert "Use staged approvals." in prompt


def test_chat_prompt_remains_general_without_ask_mode():
    service = object.__new__(ChatService)
    prompt = service._build_prompt(
        [{"role": "user", "content": "Hello"}],
        "",
        "chat",
    )

    assert "You are in Ask mode" not in prompt
    assert prompt.endswith("Assistant:")


def test_study_prompt_requests_structured_learning_material():
    service = object.__new__(ChatService)
    prompt = service._build_prompt(
        [{"role": "user", "content": "Help me study this"}],
        "[handbook.pdf]\nA deployment has three approval stages.",
        "study",
    )

    assert "Explanation" in prompt
    assert "Key points" in prompt
    assert "Flashcards" in prompt
    assert "Quick quiz" in prompt
    assert "[handbook.pdf]" in prompt


def test_plan_prompt_requests_actionable_plan_structure():
    service = object.__new__(ChatService)
    prompt = service._build_prompt(
        [{"role": "user", "content": "Help me launch this project"}],
        "[launch-guide.md]\nRelease requires a staging review.",
        "plan",
    )

    assert "Goal" in prompt
    assert "Assumptions" in prompt
    assert "Steps" in prompt
    assert "Checkpoints" in prompt
    assert "Risks" in prompt
    assert "[launch-guide.md]" in prompt