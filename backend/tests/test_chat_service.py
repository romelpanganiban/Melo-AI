from services.chat_service import ChatService


def test_process_message():

    service = ChatService()

    result = service.process_message(
        "test-session",
        "Hello Melo"
    )

    assert "response" in result


def test_get_history():

    service = ChatService()

    history = service.get_history(
        "test-session"
    )

    assert isinstance(
        history,
        list
    )