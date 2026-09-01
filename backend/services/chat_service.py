"""Chat service with database integration"""

import json
from typing import Generator

from sqlalchemy.orm import Session
from database import get_db_session, SessionRepository, MessageRepository, DocumentRepository, ChunkRepository
from services.ollama_client import OllamaClient
from services.usage_service import record_usage
from services.embedding_service import get_embedding_service
from services.qdrant_client import get_qdrant_client
from services.settings_manager import SettingsManager
from core.logging import logger
from core.errors import SessionNotFoundError, ChatServiceError
from core.settings import settings


class ChatService:
    """Service for handling chat operations with database backend"""

    _availability_checked = False

    def __init__(self, workspace_id: str = None):
        saved_settings = SettingsManager(workspace_id=workspace_id).get_settings()
        selected_model = saved_settings.get("model", settings.OLLAMA_MODEL)
        self.learning_level = saved_settings.get("learning_level", "intermediate")
        self.explanation_style = saved_settings.get("explanation_style", "clear")
        self.quiz_difficulty = saved_settings.get("quiz_difficulty", "medium")
        self.auto_model_names: list[str] = []

        self.ollama = OllamaClient(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL if selected_model == "auto" else selected_model,
            timeout=settings.OLLAMA_TIMEOUT,
            num_predict=settings.OLLAMA_NUM_PREDICT,
            keep_alive=settings.OLLAMA_KEEP_ALIVE,
            num_ctx=saved_settings.get("context_size", settings.OLLAMA_CONTEXT_SIZE),
        )

        if selected_model == "auto":
            try:
                self.auto_model_names = [item.get("name", "") for item in self.ollama.list_models()]
            except Exception:
                self.auto_model_names = []
        
        # Check Ollama availability on startup (silent, just log)
        if not ChatService._availability_checked:
            self._check_ollama_availability()
            ChatService._availability_checked = True

    def _select_auto_model(self, message: str) -> None:
        """Choose a coding model for code prompts when one is installed."""
        if not self.auto_model_names:
            return

        coding_prompt = any(
            keyword in message.lower()
            for keyword in ("code", "python", "javascript", "typescript", "bug", "debug", "function", "sql")
        )
        if coding_prompt:
            coding_models = [name for name in self.auto_model_names if "coder" in name.lower()]
            if coding_models:
                self.ollama.model = coding_models[0]
                return

        general_models = [name for name in self.auto_model_names if "qwen3:8b" == name]
        self.ollama.model = general_models[0] if general_models else self.auto_model_names[0]

    @staticmethod
    def _resolve_mode(message: str, mode: str, has_document_context: bool = False) -> str:
        """Resolve Auto mode to the most useful response policy for the request."""
        if mode != "auto":
            return mode

        normalized = message.lower()
        if any(keyword in normalized for keyword in ("quiz", "flashcard", "teach me", "study", "learn")):
            return "study"
        if any(keyword in normalized for keyword in ("plan", "roadmap", "steps", "how do i achieve", "organize")):
            return "plan"
        if has_document_context or any(keyword in normalized for keyword in ("according to", "in the document", "from my files", "what does the guide say")):
            return "ask"
        return "chat"

    def _search_documents(self, query: str, session_id: str = None, top_k: int = 5, owner_id: str = None, collection_id: str = None, workspace_id: str = None, document_id: str = None) -> dict:
        """Search for relevant documents using vector similarity
        
        Args:
            query: User query text
            session_id: Optional session ID to filter documents
            top_k: Number of top chunks to return
            
        Returns:
            Dictionary with sources list and context text, or empty if no documents or Qdrant disabled
        """
        if document_id:
            try:
                db = get_db_session()
                document = DocumentRepository(db).get_by_id(
                    document_id,
                    owner_id=owner_id,
                    workspace_id=workspace_id,
                )
                if document and (not session_id or document.session_id == session_id):
                    chunks = ChunkRepository(db).get_by_document(document_id)
                    context = "\n\n".join(
                        f"[{document.filename} | chunk {chunk.chunk_index}]\n{chunk.content}"
                        for chunk in chunks
                    ) or f"[{document.filename}]\n{document.content}"
                    return {
                        "sources": [{
                            "document_id": document.id,
                            "filename": document.filename,
                            "relevance": 100.0,
                            "chunks": [chunk.chunk_index for chunk in chunks],
                        }],
                        "context": context,
                    }
            except Exception as e:
                logger.warning(f"Direct document context lookup failed: {str(e)}")
            finally:
                if "db" in locals():
                    db.close()

        if not settings.QDRANT_ENABLED:
            return {"sources": [], "context": ""}

        try:
            qdrant_client = get_qdrant_client()
            
            # Check if Qdrant is available
            if not qdrant_client.is_available():
                logger.warning("Qdrant not available, skipping document search")
                return {"sources": [], "context": ""}
            
            # Embed the query
            embedding_service = get_embedding_service()
            query_embedding = embedding_service.embed_query(query)
            
            # Search Qdrant for similar chunks
            filters = {
                **({"session_id": session_id} if session_id else {}),
                **({"workspace_id": workspace_id} if workspace_id else {"owner_id": owner_id} if owner_id else {}),
                **({"collection_id": collection_id} if collection_id else {}),
                **({"document_id": document_id} if document_id else {}),
            } or None
            search_results = qdrant_client.search(
                query_embedding=query_embedding,
                limit=top_k,
                score_threshold=0.0 if document_id else settings.QDRANT_SCORE_THRESHOLD,
                filters=filters
            )
            
            if not search_results:
                logger.info("No documents found for query", extra={"query_len": len(query)})
                return {"sources": [], "context": ""}
            
            sources, context = self._format_search_results(search_results)
            
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

    @staticmethod
    def _format_search_results(search_results: list[dict]) -> tuple[list[dict], str]:
        """Deduplicate chunks and create stable source metadata for prompts/UI."""
        chunk_map: dict[tuple[str, int | None], dict] = {}
        source_map: dict[str, dict] = {}
        context_parts: list[str] = []

        for result in search_results:
            payload = result.get("payload") or result.get("metadata", {})
            document_id = payload.get("document_id") or result.get("document_id") or "unknown"
            chunk_index = payload.get("chunk_index", result.get("chunk_index"))
            chunk_key = (str(document_id), chunk_index)
            filename = payload.get("filename", "Unknown")
            content = result.get("content") or payload.get("content", "")
            score = float(result.get("score", result.get("similarity_score", 0)) or 0)
            existing_chunk = chunk_map.get(chunk_key)
            if existing_chunk is None or score > existing_chunk["score"]:
                chunk_map[chunk_key] = {"filename": filename, "content": content, "score": score, "chunk_index": chunk_index, "document_id": str(document_id)}

        for chunk in chunk_map.values():
            document_id = chunk["document_id"]
            filename = chunk["filename"]
            content = chunk["content"]
            score = chunk["score"]
            chunk_index = chunk["chunk_index"]
            source = source_map.setdefault(
                document_id,
                {"document_id": document_id, "filename": filename, "relevance": round(score * 100, 1), "chunks": []},
            )
            source["relevance"] = max(source["relevance"], round(score * 100, 1))
            if chunk_index is not None:
                source["chunks"].append(chunk_index)
            context_parts.append(f"[{filename} | chunk {chunk_index if chunk_index is not None else '?'}]\n{content}")

        return list(source_map.values()), "\n\n".join(context_parts)

    def _set_initial_session_title(self, session, message: str, session_repo: SessionRepository) -> None:
        """Use the first user message as the title for untouched sessions."""
        if session.title != "New Chat":
            return

        title = " ".join(message.split())
        max_title_length = 50
        if len(title) > max_title_length:
            title = f"{title[:max_title_length].rstrip()}..."
        if title:
            session_repo.update_title(session.id, title)

    def process_message(self, session_id: str, message: str, db: Session = None, mode: str = "chat", owner_id: str = None, collection_id: str = None, workspace_id: str = None, document_id: str = None) -> dict:
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
            session = session_repo.get_by_id(session_id, owner_id=owner_id, workspace_id=workspace_id)
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
            self._set_initial_session_title(session, message, session_repo)

            # Get session history for context
            history = self._get_history_dicts(session_id, db)
            
            # Search for relevant documents
            doc_search = self._search_documents(message, session_id=session_id, top_k=5, owner_id=owner_id, collection_id=collection_id, workspace_id=workspace_id, document_id=document_id)
            resolved_mode = self._resolve_mode(message, mode, bool(doc_search.get("context", "").strip()))

            # Generate response with document context
            self._select_auto_model(message)
            response = self._generate_response(
                session_id,
                history,
                doc_context=doc_search.get("context", ""),
                mode=resolved_mode,
            )

            # Store assistant response
            usage = self.ollama.last_usage
            msg_repo.create(
                session_id,
                "assistant",
                response,
                tokens_used=usage.get("total_tokens", 0),
                model_name=self.ollama.model,
            )
            record_usage(db, owner_id, workspace_id, usage.get("total_tokens", 0))

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

    def process_message_stream(self, session_id: str, message: str, db: Session = None, mode: str = "chat", owner_id: str = None, collection_id: str = None, workspace_id: str = None, document_id: str = None) -> Generator[str, None, None]:
        """Process a user message and stream assistant response chunks as NDJSON lines."""
        if db is None:
            db = get_db_session()
            should_close = True
        else:
            should_close = False

        try:
            session_repo = SessionRepository(db)
            session = session_repo.get_by_id(session_id, owner_id=owner_id, workspace_id=workspace_id)
            if not session:
                raise SessionNotFoundError(session_id)

            msg_repo = MessageRepository(db)
            msg_repo.create(session_id, "user", message)
            self._set_initial_session_title(session, message, session_repo)
            history = self._get_history_dicts(session_id, db)
            
            # Search for relevant documents
            doc_search = self._search_documents(message, session_id=session_id, top_k=5, owner_id=owner_id, collection_id=collection_id, workspace_id=workspace_id, document_id=document_id)
            resolved_mode = self._resolve_mode(message, mode, bool(doc_search.get("context", "").strip()))

            chunks: list[str] = []
            self._select_auto_model(message)
            for chunk in self._generate_response_stream(
                session_id,
                history,
                doc_context=doc_search.get("context", ""),
                mode=resolved_mode,
            ):
                if not chunk:
                    continue
                chunks.append(chunk)
                yield json.dumps({"type": "chunk", "content": chunk}) + "\n"

            response = "".join(chunks).strip()
            if not response:
                raise ChatServiceError("Ollama returned empty response")

            usage = self.ollama.last_usage
            msg_repo.create(
                session_id,
                "assistant",
                response,
                tokens_used=usage.get("total_tokens", 0),
                model_name=self.ollama.model,
            )
            record_usage(db, owner_id, workspace_id, usage.get("total_tokens", 0))
            yield json.dumps(
                {
                    "type": "done",
                    "session_id": session_id,
                    "response": response,
                    "model": self.ollama.model,
                    "usage": self.ollama.last_usage,
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

    def get_history(self, session_id: str, db: Session = None, owner_id: str = None, workspace_id: str = None) -> list[dict]:
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
            session = session_repo.get_by_id(session_id, owner_id=owner_id, workspace_id=workspace_id)
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
                {
                    "role": msg.role,
                    "content": msg.content,
                    "model": msg.model_name,
                    "usage": {
                        "prompt_tokens": 0,
                        "completion_tokens": msg.tokens_used or 0,
                        "total_tokens": msg.tokens_used or 0,
                    } if msg.role == "assistant" and msg.tokens_used is not None else None,
                }
                for msg in messages
            ]
        finally:
            if should_close:
                db.close()

    def _build_prompt(self, history: list[dict], doc_context: str, mode: str) -> str:
        context_messages = history[-10:] if len(history) > 1 else []
        context = "".join(
            f"{('User' if msg.get('role') == 'user' else 'Assistant')}: {msg.get('content', '')}\n"
            for msg in context_messages[:-1]
        )
        current_message = history[-1].get("content", "") if history else ""

        if doc_context.strip() and any(
            keyword in current_message.lower()
            for keyword in ("resume", "cv", "curriculum vitae", "revise", "rewrite", "format")
        ):
            resume_prompt = (
                "You are a professional resume editor. The uploaded document is the source resume. "
                "Revise it directly using only facts present in the document; never invent employers, dates, "
                "degrees, metrics, or skills. Return a polished, ATS-friendly resume in Markdown with these "
                "sections when supported by the source: Professional Summary, Skills, Experience, Education, "
                "Certifications, and Projects. Improve wording, grammar, consistency, and formatting. "
                "If information is missing, omit that section rather than asking the user to paste the resume. "
                "Return only the revised resume followed by a short Notes section listing any important missing details."
            )
            return f"{resume_prompt}\n\nSource resume:\n{doc_context}\n\nUser request: {current_message}\n\nRevised resume:"

        if mode == "ask":
            grounding = (
                "You are in Ask mode. The document text below was extracted from a file uploaded by the user and is available to you. "
                "Answer using only the provided document context. Never claim that you cannot access files, external files, or the user's local machine when document context is provided. "
                "If the context does not contain enough evidence, say so clearly and do not guess. "
                "Cite supporting filenames in square brackets, for example [guide.pdf]."
            )
            context_block = doc_context.strip() or "No relevant document context was found."
            return f"{grounding}\n\n{context}User: {current_message}\n\nDocument context:\n{context_block}\n\nAssistant:"

        if mode == "study":
            context_block = doc_context.strip() or "No relevant document context was found."
            study_prompt = (
                "You are in Study mode. Teach the topic clearly using the document context. "
                "Do not invent facts beyond the context. Structure your response with these headings: "
                "Explanation, Key points, Flashcards, and Quick quiz. Include answers after the quiz. "
                "Cite supporting filenames in square brackets when using the documents. "
                f"Adapt the explanation for a {getattr(self, 'learning_level', 'intermediate')} learner, "
                f"use a {getattr(self, 'explanation_style', 'clear')} explanation style, "
                f"and make the quiz {getattr(self, 'quiz_difficulty', 'medium')} difficulty."
            )
            return f"{study_prompt}\n\n{context}User: {current_message}\n\nDocument context:\n{context_block}\n\nAssistant:"

        if mode == "plan":
            context_block = doc_context.strip() or "No relevant document context was found."
            plan_prompt = (
                "You are in Plan mode. Convert the user's goal into a practical ordered plan. "
                "Use document context as evidence when available and do not invent constraints. "
                "Structure the response with these headings: Goal, Assumptions, Steps, Checkpoints, and Risks. "
                "Make each step specific and actionable, and cite supporting filenames in square brackets."
            )
            return f"{plan_prompt}\n\n{context}User: {current_message}\n\nDocument context:\n{context_block}\n\nAssistant:"

        if mode == "agent":
            context_block = doc_context.strip() or "No relevant document context was found."
            agent_prompt = (
                "You are in Agent mode. Break the user's goal into a numbered sequence of concrete steps. "
                "For each step include the intended tool or information source, expected result, and whether user approval is required. "
                "Do not execute tools, modify files, delete data, or run Git actions. "
                "Structure the response with these headings: Objective, Proposed steps, Approval points, and Open questions."
            )
            return f"{agent_prompt}\n\n{context}User: {current_message}\n\nDocument context:\n{context_block}\n\nAssistant:"

        if doc_context.strip():
            grounding = (
                "The document text below was extracted from a file uploaded by the user and is available to you. "
                "Use it to answer the user. Do not say that you cannot access or analyze files."
            )
            return f"{grounding}\n\n{context}User: {current_message}\n\nContext from documents:\n{doc_context}\n\nAssistant:"
        return f"{context}User: {current_message}\nAssistant:"

    def _generate_response(self, session_id: str, history: list[dict], doc_context: str = "", mode: str = "chat") -> str:
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
            prompt = self._build_prompt(history, doc_context, mode)
            
            logger.info(
                "Generating response with Ollama",
                extra={
                    "session_id": session_id,
                    "model": settings.OLLAMA_MODEL,
                    "context_length": len(prompt),
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

    def _generate_response_stream(self, session_id: str, history: list[dict], doc_context: str = "", mode: str = "chat") -> Generator[str, None, None]:
        """Generate streaming response chunks from Ollama.
        
        Args:
            session_id: Session identifier
            history: Chat history
            doc_context: Optional document context from RAG search
            
        Yields:
            Response chunks as they are generated
        """
        try:
            prompt = self._build_prompt(history, doc_context, mode)

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