from memory.memory_manager import MemoryManager
from memory.session_manager import SessionManager
from services.ollama_client import OllamaClient
from core.logging import logger
from core.errors import SessionNotFoundError, ChatServiceError
from core.settings import settings


class ChatService:
    """Service for handling chat operations"""

    def __init__(self):
        self.memory = MemoryManager()
        self.session_manager = SessionManager()
        
        # Initialize Ollama client
        self.ollama = OllamaClient(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            timeout=settings.OLLAMA_TIMEOUT
        )
        
        # Check Ollama availability on startup
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
            if not self._session_exists(session_id):
                raise SessionNotFoundError(session_id)
            
            logger.info(
                f"Message received",
                extra={
                    "session_id": session_id,
                    "message_length": len(message)
                }
            )

            # Store user message
            self.memory.add_message(session_id, "user", message)

            # Get session history for context
            history = self.memory.get_session_history(session_id)

            # Generate response (placeholder - will be replaced with real LLM)
            response = self._generate_response(session_id, history)

            # Store assistant response
            self.memory.add_message(session_id, "assistant", response)

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
            if not self._session_exists(session_id):
                raise SessionNotFoundError(session_id)
            
            logger.info(
                f"Retrieving chat history",
                extra={"session_id": session_id}
            )
            
            history = self.memory.get_session_history(session_id)
            return history
            
        except SessionNotFoundError:
            raise
        except Exception as e:
            logger.error(
                f"Error retrieving history: {str(e)}",
                extra={"session_id": session_id}
            )
            raise ChatServiceError(f"Failed to retrieve history: {str(e)}")

    def _session_exists(self, session_id: str) -> bool:
        """Check if a session exists
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session exists, False otherwise
        """
        try:
            sessions = self.session_manager.get_sessions()
            return any(s.get("id") == session_id for s in sessions)
        except Exception as e:
            logger.warning(
                f"Error checking session existence: {str(e)}",
                extra={"session_id": session_id}
            )
            return False

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
        """Check Ollama availability and log warnings if not available"""
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