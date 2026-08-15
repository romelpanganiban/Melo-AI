from sqlalchemy.orm import Session
from database import SessionRepository, get_db_session
from core.logging import logger
from core.errors import SessionNotFoundError, ChatServiceError


class SessionService:
    """Service for handling session operations with database backend"""

    def create_session(self, db: Session = None) -> dict:
        """Create a new session
        
        Returns:
            Dictionary with session id and title
        """
        if db is None:
            db = get_db_session()
            should_close = True
        else:
            should_close = False
        try:
            repo = SessionRepository(db)
            session = repo.create(title="New Chat")
            logger.info(
                f"Session created",
                extra={"session_id": session.id}
            )
            return {
                "id": session.id,
                "title": session.title
            }
            
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            raise ChatServiceError(f"Failed to create session: {str(e)}")
        finally:
            if should_close:
                db.close()

    def get_sessions(self, db: Session = None) -> list[dict]:
        """Get all sessions
        
        Returns:
            List of sessions
        """
        if db is None:
            db = get_db_session()
            should_close = True
        else:
            should_close = False
        try:
            repo = SessionRepository(db)
            sessions = repo.get_all()
            logger.info(
                f"Sessions retrieved",
                extra={"count": len(sessions)}
            )
            return [
                {"id": s.id, "title": s.title}
                for s in sessions
            ]
            
        except Exception as e:
            logger.error(f"Error retrieving sessions: {str(e)}")
            raise ChatServiceError(f"Failed to retrieve sessions: {str(e)}")
        finally:
            if should_close:
                db.close()

    def rename_session(self, session_id: str, title: str, db: Session = None) -> dict:
        """Rename a session
        
        Args:
            session_id: Session identifier
            title: New session title
            db: Optional database session (uses default if None)
            
        Returns:
            Updated session dictionary
            
        Raises:
            SessionNotFoundError: If session not found
        """
        if db is None:
            db = get_db_session()
            should_close = True
        else:
            should_close = False
        try:
            repo = SessionRepository(db)
            session = repo.update_title(session_id, title)
            
            logger.info(
                f"Session renamed",
                extra={"session_id": session_id, "new_title": title}
            )
            return {
                "id": session.id,
                "title": session.title
            }
            
        except SessionNotFoundError:
            raise
        except Exception as e:
            logger.error(
                f"Error renaming session: {str(e)}",
                extra={"session_id": session_id}
            )
            raise ChatServiceError(f"Failed to rename session: {str(e)}")
        finally:
            if should_close:
                db.close()

    def delete_session(self, session_id: str, db: Session = None) -> None:
        """Delete a session
        
        Args:
            session_id: Session identifier
            db: Optional database session (uses default if None)
            
        Raises:
            SessionNotFoundError: If session not found
        """
        if db is None:
            db = get_db_session()
            should_close = True
        else:
            should_close = False
        try:
            repo = SessionRepository(db)
            repo.delete(session_id)
            
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
            raise ChatServiceError(f"Failed to delete session: {str(e)}")
        finally:
            if should_close:
                db.close()