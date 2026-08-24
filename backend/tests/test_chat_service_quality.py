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