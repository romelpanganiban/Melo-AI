from memory.session_manager import SessionManager


def test_create_session():

    manager = SessionManager()

    session = manager.create_session()

    assert "id" in session
    assert "title" in session