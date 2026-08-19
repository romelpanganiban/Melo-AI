from types import SimpleNamespace
from unittest.mock import Mock

from services.chat_service import ChatService


def test_initial_session_title_uses_first_message():
    service = ChatService.__new__(ChatService)
    session = SimpleNamespace(id="session-1", title="New Chat")
    session_repo = Mock()

    service._set_initial_session_title(
        session,
        "  Best practices for creating SaaS products?  ",
        session_repo,
    )

    session_repo.update_title.assert_called_once_with(
        "session-1", "Best practices for creating SaaS products?"
    )


def test_initial_session_title_preserves_manual_title():
    service = ChatService.__new__(ChatService)
    session = SimpleNamespace(id="session-1", title="My Project")
    session_repo = Mock()

    service._set_initial_session_title(session, "A new question", session_repo)

    session_repo.update_title.assert_not_called()
