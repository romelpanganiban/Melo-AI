"""Chat service with database integration"""

from sqlalchemy.orm import Session as DBSession
from services.ollama_client import OllamaClient
from database.repositories import MessageRepository, SessionRepository
from core.logging import logger
from core.errors import SessionNotFoundError, ChatServiceError
from core.settings import settings


class ChatServiceDB:
    """Service for handling chat operations with database backend"""

    def __init__(self, db: DBSession):
        self.db = db
        self.message_repo = MessageRepository(db)
        self.session_repo = SessionRepository(db)
        
        # Initialize Ollama client
        self.ollama = OllamaClient(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            timeout=settings.OLLAMA_TIMEOUT
        )
        
        # Check Ollama availability on startup (silent, just log)
        self._check_ollama_availability()

    def process_message(self, session_id: str, message: str) -> dict:
        """Process a user message
        
        Args:
            session_id: Session identifier
            message: User message text
            
        Returns:
            Dictionary with response and recent history
            
        Raises:
            SessionNotFoundError: If session doesn't exist
            ChatServiceError: If message processing fails
        """
        try:
            # Validate session exists
            session = self.session_repo.get_by_id(session_id)
            if not session:
                raise SessionNotFoundError(session_id)
            
            logger.info(
                "Message received",
                extra={
                    "session_id": session_id,
                    "message_length": len(message)
                }
            )

            # Store user message
            self.message_repo.create(session_id, "user", message)

            # Get session history for context
            history = self._get_history_dicts(session_id)

            # Generate response
            response = self._generate_response(session_id, history)

            # Store assistant response
            self.message_repo.create(session_id, "assistant", response)

            logger.info(
                "Response generated",
                extra={"session_id": session_id}
            )

            return {
                "response": response,
                "recent_history": history[-5:],
                "session_id": session_id
            }
            
        except SessionNotFoundError:
            raise
        except Exception as e:
            logger.error(
                f"Error processing message: {str(e)}",
                extra={"session_id": session_id}
            )
            raise ChatServiceError(f"Failed to process message: {str(e)}")

    def get_history(self, session_id: str) -> list[dict]:
        """Get chat history for a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of messages
            
        Raises:
            SessionNotFoundError: If session doesn't exist
            ChatServiceError: If retrieval fails
        """
        try:
            # Validate session exists
            session = self.session_repo.get_by_id(session_id)
            if not session:
                raise SessionNotFoundError(session_id)
            
            logger.info(
                "Retrieving chat history",
                extra={"session_id": session_id}
            )
            
            return self._get_history_dicts(session_id)
            
        except SessionNotFoundError:
            raise
        except Exception as e:
            logger.error(
                f"Error retrieving history: {str(e)}",
                extra={"session_id": session_id}
            )
            raise ChatServiceError(f"Failed to retrieve history: {str(e)}")

    def _get_history_dicts(self, session_id: str) -> list[dict]:
        """Get history as list of dictionaries
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of message dictionaries
        """
        messages = self.message_repo.get_by_session(session_id)
        return [
            {
                "role": msg.role,
                "content": msg.content
            }
            for msg in messages
        ]

    def _generate_response(self, session_id: str, history: list[dict]) -> str:
        """Generate response using Ollama LLM
        
        Args:
            session_id: Session identifier
            history: Chat history
            
        Returns:
            Generated response text
            
        Raises:
            ChatServiceError: If generation fails
        """
        try:
            # Build context from recent history (last 10 messages)
            context_messages = history[-10:] if len(history) > 1 else []
            
            # Format conversation context
            context = ""
            for msg in context_messages[:-1]:  # Exclude the current user message
                role = "User" if msg.get("role") == "user" else "Assistant"
                context += f"{role}: {msg.get('content', '')}\n"
            
            # Get the current user message (last message in history)
            current_message = history[-1].get("content", "") if history else ""
            
            # Build prompt with context
            prompt = f"{context}User: {current_message}\nAssistant:"
            
            logger.info(
                "Generating response with Ollama",
                extra={
                    "session_id": session_id,
                    "model": settings.OLLAMA_MODEL,
                    "context_length": len(context)
                }
            )
            
            # Generate response using Ollama
            response = self.ollama.generate_response(
                prompt=prompt,
                system_prompt=settings.SYSTEM_PROMPT,
                temperature=settings.OLLAMA_TEMPERATURE,
                top_p=settings.OLLAMA_TOP_P,
                top_k=settings.OLLAMA_TOP_K
            )
            
            return response.strip()
            
        except ChatServiceError:
            raise
        except Exception as e:
            logger.error(
                f"Error generating response: {str(e)}",
                extra={"session_id": session_id}
            )
            raise ChatServiceError(f"Failed to generate response: {str(e)}")
    
    def _check_ollama_availability(self) -> None:
        """Check Ollama availability and log info"""
        if not self.ollama.is_available():
            logger.warning(
                f"Ollama server not available at {settings.OLLAMA_BASE_URL}",
                extra={
                    "base_url": settings.OLLAMA_BASE_URL,
                    "model": settings.OLLAMA_MODEL
                }
            )
            return
        
        if not self.ollama.is_model_available():
            logger.warning(
                f"Model not available: {settings.OLLAMA_MODEL}",
                extra={
                    "model": settings.OLLAMA_MODEL,
                    "base_url": settings.OLLAMA_BASE_URL
                }
            )
            return
        
        logger.info(
            f"Ollama is ready with model: {settings.OLLAMA_MODEL}",
            extra={
                "base_url": settings.OLLAMA_BASE_URL,
                "model": settings.OLLAMA_MODEL
            }
        )
