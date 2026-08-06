from memory.session_manager import SessionManager
from core.logger import logger


class SessionService:

    def __init__(self):
        self.manager = SessionManager()

    def create_session(self):

        session = self.manager.create_session()

        logger.info(
            f"Session created: {session['id']}"
        )

        return session

    def get_sessions(self):
        return self.manager.get_sessions()

    def rename_session(
        self,
        session_id,
        title
    ):

        logger.info(
            f"Session renamed: {session_id}"
        )

        return self.manager.rename_session(
            session_id,
            title
        )

    def delete_session(
        self,
        session_id
    ):

        logger.info(
            f"Session deleted: {session_id}"
        )

        return self.manager.delete_session(
            session_id
        )