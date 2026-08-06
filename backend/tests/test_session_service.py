from services.session_service import SessionService


def test_create_session():

    service = SessionService()

    session = service.create_session()

    assert "id" in session


def test_get_sessions():

    service = SessionService()

    sessions = service.get_sessions()

    assert isinstance(
        sessions,
        list
    )