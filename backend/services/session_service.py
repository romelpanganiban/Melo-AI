from memory.session_manager import SessionManager
from core.logging import logger
from core.errors import SessionNotFoundError


class SessionService:
    """Service for handling session operations"""

    def __init__(self):
        self.manager = SessionManager()

    def create_session(self) -> dict:
        """Create a new session
        
        Returns:
            Dictionary with session id and title
        """
        try:
            session = self.manager.create_session()
            logger.info(
                f"Session created",
                extra={"session_id": session['id']}
            )
            return session
            
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            raise

    def get_sessions(self) -> list[dict]:
        """Get all sessions
        
        Returns:
            List of sessions
        """
        try:
            sessions = self.manager.get_sessions()
            logger.info(
                f"Sessions retrieved",
                extra={"count": len(sessions)}
            )
            return sessions
            
        except Exception as e:
            logger.error(f"Error retrieving sessions: {str(e)}")
            raise

    def rename_session(self, session_id: str, title: str) -> dict:
        """Rename a session
        
        Args:
            session_id: Session identifier
            title: New session title
            
        Returns:
            Updated session dictionary
            
        Raises:
            SessionNotFoundError: If session not found
        """
        try:
            session = self.manager.rename_session(session_id, title)
            
            if session is None:
                raise SessionNotFoundError(session_id)
            
            logger.info(
                f"Session renamed",
                extra={"session_id": session_id, "new_title": title}
            )
            return session
            
        except SessionNotFoundError:
            raise
        except Exception as e:
            logger.error(
                f"Error renaming session: {str(e)}",
                extra={"session_id": session_id}
            )
            raise

    def delete_session(self, session_id: str) -> None:
        """Delete a session
        
        Args:
            session_id: Session identifier
            
        Raises:
            SessionNotFoundError: If session not found
        """
        try:
            result = self.manager.delete_session(session_id)
            
            if result is None:
                raise SessionNotFoundError(session_id)
            
            logger.info(
                f"Session deleted",
                extra={"session_id": session_id}
            )
            
        except SessionNotFoundError:
            raise
        except Exception as e:
            logger.error(
                f"Error deleting session: {str(e)}",
                extra={"session_id": session_id}
            )
            raise