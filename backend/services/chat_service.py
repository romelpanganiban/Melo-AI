"""Chat service with database integration"""

import json
from typing import Generator

from sqlalchemy.orm import Session
from database import get_db_session, SessionRepository, MessageRepository
from services.ollama_client import OllamaClient
from services.embedding_service import get_embedding_service
from services.qdrant_client import get_qdrant_client
from core.logging import logger
from core.errors import SessionNotFoundError, ChatServiceError
from core.settings import settings


class ChatService:
    """Service for handling chat operations with database backend"""

    _availability_checked = False

    def __init__(self):
        # Initialize Ollama client
        self.ollama = OllamaClient(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            timeout=settings.OLLAMA_TIMEOUT
        )
        
        # Check Ollama availability on startup (silent, just log)
        if not ChatService._availability_checked:
            self._check_ollama_availability()
            ChatService._availability_checked = True

    def _search_documents(self, query: str, session_id: str = None, top_k: int = 5) -> dict:
        """Search for relevant documents using vector similarity
        
        Args:
            query: User query text
            session_id: Optional session ID to filter documents
            top_k: Number of top chunks to return
            
        Returns:
            Dictionary with sources list and context text, or empty if no documents or Qdrant disabled
        """
        if not settings.QDRANT_ENABLED:
            return {"sources": [], "context": ""}
        
        try:
            embedding_service = get_embedding_service()
            qdrant_client = get_qdrant_client()
            
            # Check if Qdrant is available
            if not qdrant_client.is_available():
                logger.warning("Qdrant not available, skipping document search")
                return {"sources": [], "context": ""}
            
            # Embed the query
            query_embedding = embedding_service.embed_query(query)
            
            # Search Qdrant for similar chunks
            search_results = qdrant_client.search(
                query_embedding=query_embedding,
                limit=top_k,
                score_threshold=0.5,
                filters={"session_id": session_id} if session_id else None
            )
            
            if not search_results:
                logger.info("No documents found for query", extra={"query_len": len(query)})
                return {"sources": [], "context": ""}
            
            # Build context from search results
            sources = []
            context_parts = []
            
            for result in search_results:
                payload = result.get("payload", {})
                filename = payload.get("filename", "Unknown")
                content = payload.get("content", "")
                score = result.get("score", 0)
                
                # Track unique sources
                source_key = f"{filename}"
                if source_key not in [s.get("filename") for s in sources]:
                    sources.append({
                        "filename": filename,
                        "relevance": round(score * 100, 1)
                    })
                
                # Add to context
                context_parts.append(f"[{filename}]\n{content}")
            
            context = "\n\n".join(context_parts)
            
            logger.info(
                "Document search completed",
                extra={
                    "query_len": len(query),
                    "results_count": len(search_results),
                    "sources_count": len(sources)
                }
            )
            
            return {
                "sources": sources,
                "context": context
            }
            
        except Exception as e:
            logger.error(
                f"Document search failed: {str(e)}",
                extra={"query_len": len(query)}
            )
            # Return empty results on error instead of failing
            return {"sources": [], "context": ""}

    def process_message(self, session_id: str, message: str, db: Session = None) -> dict:
        """Process a user message
        
        Args:
            session_id: Session identifier
            message: User message text
            db: Optional database session (uses default if None)
            
        Returns:
            Dictionary with response, recent history, and sources
            
        Raises:
            SessionNotFoundError: If session doesn't exist
            ChatServiceError: If message processing fails
        """
        if db is None:
            db = get_db_session()
            should_close = True
        else:
            should_close = False
            
        try:
            # Validate session exists
            session_repo = SessionRepository(db)
            session = session_repo.get_by_id(session_id)
            if not session:
                raise SessionNotFoundError(session_id)
            
            logger.info(
                f"Message received",
                extra={
                    "session_id": session_id,
                    "message_length": len(message)
                }
            )

            # Store user message
            msg_repo = MessageRepository(db)
            msg_repo.create(session_id, "user", message)

            # Get session history for context
            history = self._get_history_dicts(session_id, db)
            
            # Search for relevant documents
            doc_search = self._search_documents(message, session_id=session_id, top_k=5)

            # Generate response with document context
            response = self._generate_response(session_id, history, doc_context=doc_search.get("context", ""))

            # Store assistant response
            msg_repo.create(session_id, "assistant", response)

            logger.info(
                "Response generated",
                extra={"session_id": session_id}
            )

            return {
                "session_id": session_id,
                "response": response,
                "recent_history": history[-5:],
                "sources": doc_search.get("sources", [])
            }
            
        except SessionNotFoundError:
            raise
        except Exception as e:
            logger.error(
                f"Error processing message: {str(e)}",
                extra={"session_id": session_id}
            )
            raise ChatServiceError(f"Failed to process message: {str(e)}")
        finally:
            if should_close:
                db.close()

    def process_message_stream(self, session_id: str, message: str, db: Session = None) -> Generator[str, None, None]:
        """Process a user message and stream assistant response chunks as NDJSON lines."""
        if db is None:
            db = get_db_session()
            should_close = True
        else:
            should_close = False

        try:
            session_repo = SessionRepository(db)
            session = session_repo.get_by_id(session_id)
            if not session:
                raise SessionNotFoundError(session_id)

            msg_repo = MessageRepository(db)
            msg_repo.create(session_id, "user", message)
            history = self._get_history_dicts(session_id, db)
            
            # Search for relevant documents
            doc_search = self._search_documents(message, session_id=session_id, top_k=5)

            chunks: list[str] = []
            for chunk in self._generate_response_stream(session_id, history, doc_context=doc_search.get("context", "")):
                if not chunk:
                    continue
                chunks.append(chunk)
                yield json.dumps({"type": "chunk", "content": chunk}) + "\n"

            response = "".join(chunks).strip()
            if not response:
                raise ChatServiceError("Ollama returned empty response")

            msg_repo.create(session_id, "assistant", response)
            yield json.dumps(
                {
                    "type": "done",
                    "session_id": session_id,
                    "response": response,
                    "sources": doc_search.get("sources", [])
                }
            ) + "\n"

        except SessionNotFoundError as e:
            yield json.dumps(
                {
                    "type": "error",
                    "error_code": "SESSION_NOT_FOUND",
                    "message": str(e),
                }
            ) + "\n"
        except Exception as e:
            logger.error(
                f"Error processing streaming message: {str(e)}",
                extra={"session_id": session_id}
            )
            yield json.dumps(
                {
                    "type": "error",
                    "error_code": "CHAT_SERVICE_ERROR",
                    "message": f"Failed to process message: {str(e)}",
                }
            ) + "\n"
        finally:
            if should_close:
                db.close()

    def get_history(self, session_id: str, db: Session = None) -> list[dict]:
        """Get chat history for a session
        
        Args:
            session_id: Session identifier
            db: Optional database session (uses default if None)
            
        Returns:
            List of messages
            
        Raises:
            SessionNotFoundError: If session doesn't exist
            ChatServiceError: If retrieval fails
        """
        if db is None:
            db = get_db_session()
            should_close = True
        else:
            should_close = False
        
        try:
            # Validate session exists
            session_repo = SessionRepository(db)
            session = session_repo.get_by_id(session_id)
            if not session:
                raise SessionNotFoundError(session_id)
            
            logger.info(
                f"Retrieving chat history",
                extra={"session_id": session_id}
            )
            
            history = self._get_history_dicts(session_id, db)
            return history
            
        except SessionNotFoundError:
            raise
        except Exception as e:
            logger.error(
                f"Error retrieving history: {str(e)}",
                extra={"session_id": session_id}
            )
            raise ChatServiceError(f"Failed to retrieve history: {str(e)}")
        finally:
            if should_close:
                db.close()

    def _get_history_dicts(self, session_id: str, db=None) -> list[dict]:
        """Get chat history as list of dicts
        
        Args:
            session_id: Session identifier
            db: Database session (optional, creates new if not provided)
            
        Returns:
            List of message dictionaries with role and content
        """
        if db is None:
            db = get_db_session()
            should_close = True
        else:
            should_close = False
        
        try:
            msg_repo = MessageRepository(db)
            messages = msg_repo.get_by_session(session_id)
            
            return [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
        finally:
            if should_close:
                db.close()

    def _generate_response(self, session_id: str, history: list[dict], doc_context: str = "") -> str:
        """Generate response using Ollama LLM
        
        Args:
            session_id: Session identifier
            history: Chat history
            doc_context: Optional document context from RAG search
            
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
            
            # Build prompt with document context if available
            if doc_context.strip():
                prompt = f"{context}User: {current_message}\n\nContext from documents:\n{doc_context}\n\nAssistant:"
            else:
                prompt = f"{context}User: {current_message}\nAssistant:"
            
            logger.info(
                "Generating response with Ollama",
                extra={
                    "session_id": session_id,
                    "model": settings.OLLAMA_MODEL,
                    "context_length": len(context),
                    "has_doc_context": len(doc_context.strip()) > 0
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

    def _generate_response_stream(self, session_id: str, history: list[dict], doc_context: str = "") -> Generator[str, None, None]:
        """Generate streaming response chunks from Ollama.
        
        Args:
            session_id: Session identifier
            history: Chat history
            doc_context: Optional document context from RAG search
            
        Yields:
            Response chunks as they are generated
        """
        try:
            context_messages = history[-10:] if len(history) > 1 else []

            context = ""
            for msg in context_messages[:-1]:
                role = "User" if msg.get("role") == "user" else "Assistant"
                context += f"{role}: {msg.get('content', '')}\n"

            current_message = history[-1].get("content", "") if history else ""
            
            # Build prompt with document context if available
            if doc_context.strip():
                prompt = f"{context}User: {current_message}\n\nContext from documents:\n{doc_context}\n\nAssistant:"
            else:
                prompt = f"{context}User: {current_message}\nAssistant:"

            for chunk in self.ollama.generate_response_stream(
                prompt=prompt,
                system_prompt=settings.SYSTEM_PROMPT,
                temperature=settings.OLLAMA_TEMPERATURE,
                top_p=settings.OLLAMA_TOP_P,
                top_k=settings.OLLAMA_TOP_K,
            ):
                yield chunk

        except ChatServiceError:
            raise
        except Exception as e:
            logger.error(
                f"Error generating streaming response: {str(e)}",
                extra={"session_id": session_id}
            )
            raise ChatServiceError(f"Failed to generate streaming response: {str(e)}")
    
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