from memory.session_manager import SessionManager


class SessionService:

    def __init__(self):
        self.manager = SessionManager()

    def create_session(self):
        return self.manager.create_session()

    def get_sessions(self):
        return self.manager.get_sessions()

    def rename_session(
        self,
        session_id,
        title
    ):
        return self.manager.rename_session(
            session_id,
            title
        )

    def delete_session(
        self,
        session_id
    ):
        return self.manager.delete_session(
            session_id
        )