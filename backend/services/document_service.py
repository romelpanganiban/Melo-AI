"""Document service for knowledge base operations"""

from __future__ import annotations

import re

from database import DocumentRepository, ChunkRepository, KnowledgeCollectionRepository, get_db_session
from services.embedding_service import get_embedding_service
from services.qdrant_client import get_qdrant_client
from core.logging import logger
from core.errors import SessionNotFoundError, ChatServiceError, ValidationError
from core.settings import settings


class DocumentService:
    """Service for handling document operations"""

    def chunk_text(
        self,
        content: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 150,
    ) -> list[str]:
        """Split text into overlapping chunks using only standard library tools."""
        if chunk_size <= 0:
            raise ValidationError("chunk_size must be greater than 0", field="chunk_size")

        if chunk_overlap < 0:
            raise ValidationError("chunk_overlap must be 0 or greater", field="chunk_overlap")

        if chunk_overlap >= chunk_size:
            raise ValidationError(
                "chunk_overlap must be smaller than chunk_size",
                field="chunk_overlap",
            )

        normalized = re.sub(r"\s+", " ", content).strip()
        if not normalized:
            return []

        if len(normalized) <= chunk_size:
            return [normalized]

        chunks: list[str] = []
        start = 0

        while start < len(normalized):
            end = min(start + chunk_size, len(normalized))
            chunk = normalized[start:end].strip()
            if chunk:
                chunks.append(chunk)

            if end >= len(normalized):
                break

            start = max(end - chunk_overlap, start + 1)

        return chunks

    def upload_document(self, filename: str, file_type: str, content: str, session_id: str = None, collection_id: str = None) -> dict:
        """Upload a document
        
        Args:
            filename: Name of the document file
            file_type: Type of file (pdf, docx, txt)
            content: Document content text
            session_id: Optional session ID to associate document with
            
        Returns:
            Dictionary with document id and filename
            
        Raises:
            ValidationError: If inputs are invalid
            ChatServiceError: If upload fails
        """
        db = get_db_session()
        try:
            # Validate inputs
            if not filename or not filename.strip():
                raise ValidationError("filename is required")
            
            if file_type not in ["pdf", "docx", "txt"]:
                raise ValidationError("file_type must be 'pdf', 'docx', or 'txt'")
            
            if not content or not content.strip():
                raise ValidationError("content is required")
            
            repo = DocumentRepository(db)
            chunk_repo = ChunkRepository(db)
            document = repo.create(
                filename=filename,
                file_type=file_type,
                content=content,
                session_id=session_id,
                collection_id=collection_id,
            )

            chunks = self.chunk_text(content)
            chunk_payload = [
                {
                    "chunk_index": index,
                    "content": chunk,
                    "tokens": len(chunk.split()),
                }
                for index, chunk in enumerate(chunks)
            ]

            if chunk_payload:
                chunk_repo.create_many(document.id, chunk_payload)
                
                # Generate embeddings for chunks and store in Qdrant (if enabled)
                if settings.QDRANT_ENABLED:
                    try:
                        embedding_service = get_embedding_service()
                        qdrant_client = get_qdrant_client()
                        
                        # Extract chunk texts
                        chunk_texts = [chunk["content"] for chunk in chunk_payload]
                        
                        # Generate embeddings for all chunks at once (more efficient)
                        logger.info(
                            f"Generating embeddings for {len(chunk_texts)} chunks",
                            extra={"doc_id": document.id}
                        )
                        embeddings = embedding_service.embed_texts(chunk_texts)
                        
                        # Store embeddings in Qdrant
                        for chunk_index, (chunk_text, embedding) in enumerate(zip(chunk_texts, embeddings)):
                            qdrant_client.upsert_vector(
                                document_id=document.id,
                                chunk_index=chunk_index,
                                embedding=embedding,
                                payload={
                                    "content": chunk_text,
                                    "filename": filename,
                                    "file_type": file_type,
                                    "session_id": session_id,
                                    "chunk_index": chunk_index,
                                    "tokens": len(chunk_text.split())
                                }
                            )
                        
                        logger.info(
                            f"Embeddings stored in Qdrant",
                            extra={
                                "doc_id": document.id,
                                "chunk_count": len(chunk_payload)
                            }
                        )
                    except Exception as e:
                        # Log embedding error but don't fail the upload
                        logger.error(
                            f"Failed to store embeddings: {str(e)}",
                            extra={"doc_id": document.id}
                        )

            document.chunk_count = len(chunk_payload)
            db.commit()
            db.refresh(document)
            
            logger.info(
                f"Document uploaded",
                extra={
                    "document_id": document.id,
                    "doc_filename": filename,
                    "file_type": file_type,
                    "chunk_count": document.chunk_count,
                }
            )
            
            return {
                "id": document.id,
                "filename": document.filename,
                "file_type": document.file_type,
                "chunk_count": document.chunk_count,
                "collection_id": document.collection_id,
                "created_at": document.created_at.isoformat() if document.created_at else None
            }
            
        except ValidationError:
            raise
        except Exception as e:
            error_msg = str(e)
            # Hide technical details from user, show friendly message
            if "LogRecord" in error_msg or "overwrite" in error_msg:
                user_friendly_msg = "Failed to save document to database. Please try again or contact support if the problem persists."
            elif "filename" in error_msg.lower():
                user_friendly_msg = "The filename format is invalid. Please use a valid filename."
            else:
                user_friendly_msg = "Failed to upload document. Please check your file and try again."
            
            logger.error(f"Document upload failed: {error_msg}")
            raise ChatServiceError(user_friendly_msg)
        finally:
            db.close()

    def get_document(self, document_id: str) -> dict:
        """Get a document by ID
        
        Args:
            document_id: Document identifier
            
        Returns:
            Dictionary with document details
            
        Raises:
            ChatServiceError: If document not found or retrieval fails
        """
        db = get_db_session()
        try:
            repo = DocumentRepository(db)
            document = repo.get_by_id(document_id)
            
            if not document:
                raise ChatServiceError(f"Document not found: {document_id}")
            
            logger.info(
                f"Document retrieved",
                extra={"document_id": document_id}
            )
            
            return {
                "id": document.id,
                "filename": document.filename,
                "file_type": document.file_type,
                "content": document.content,
                "chunk_count": document.chunk_count,
                "created_at": document.created_at.isoformat() if document.created_at else None
            }
            
        except ChatServiceError:
            raise
        except Exception as e:
            logger.error(f"Error getting document: {str(e)}")
            raise ChatServiceError(f"Failed to get document: {str(e)}")
        finally:
            db.close()

    def get_session_documents(self, session_id: str) -> list[dict]:
        """Get all documents for a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of document dictionaries
            
        Raises:
            ChatServiceError: If retrieval fails
        """
        db = get_db_session()
        try:
            repo = DocumentRepository(db)
            documents = repo.get_by_session(session_id)
            
            logger.info(
                f"Session documents retrieved",
                extra={"session_id": session_id, "count": len(documents)}
            )
            
            return [
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "file_type": doc.file_type,
                    "chunk_count": doc.chunk_count,
                    "collection_id": doc.collection_id,
                    "created_at": doc.created_at.isoformat() if doc.created_at else None
                }
                for doc in documents
            ]
            
        except Exception as e:
            logger.error(f"Error getting session documents: {str(e)}")
            raise ChatServiceError(f"Failed to get session documents: {str(e)}")
        finally:
            db.close()

    def search_documents(self, query: str, session_id: str, collection_id: str = None, top_k: int = 5) -> dict:
        """Search the session's indexed knowledge without generating a chat response."""
        if not query or not query.strip():
            raise ValidationError("query is required", field="query")
        if not settings.QDRANT_ENABLED:
            return {"query": query.strip(), "results": [], "available": False}

        try:
            qdrant_client = get_qdrant_client()
            if not qdrant_client.is_available():
                return {"query": query.strip(), "results": [], "available": False}

            embedding = get_embedding_service().embed_query(query.strip())
            filters = {"session_id": session_id} if session_id else None
            if collection_id:
                filters = {"collection_id": collection_id}
            matches = qdrant_client.search(
                query_embedding=embedding,
                limit=top_k,
                score_threshold=settings.QDRANT_SCORE_THRESHOLD,
                filters=filters,
            )
            results = []
            for match in matches:
                payload = match.get("payload") or match.get("metadata", {})
                results.append({
                    "filename": payload.get("filename", "Unknown"),
                    "content": match.get("content") or payload.get("content", ""),
                    "relevance": round(match.get("score", match.get("similarity_score", 0)) * 100, 1),
                    "chunk_index": payload.get("chunk_index"),
                })
            return {"query": query.strip(), "results": results, "available": True}
        except Exception as e:
            logger.error("Document search failed", extra={"query_len": len(query)})
            raise ChatServiceError("Failed to search documents") from e

    def get_collections(self) -> list[dict]:
        db = get_db_session()
        try:
            collections = KnowledgeCollectionRepository(db).get_all()
            return [{"id": item.id, "name": item.name, "description": item.description, "created_at": item.created_at.isoformat()} for item in collections]
        finally:
            db.close()

    def create_collection(self, name: str, description: str = None) -> dict:
        db = get_db_session()
        try:
            if not name or not name.strip():
                raise ValidationError("name is required", field="name")
            collection = KnowledgeCollectionRepository(db).create(name.strip(), description.strip() if description else None)
            return {"id": collection.id, "name": collection.name, "description": collection.description, "created_at": collection.created_at.isoformat()}
        finally:
            db.close()

    def delete_document(self, document_id: str) -> None:
        """Delete a document
        
        Args:
            document_id: Document identifier
            
        Raises:
            ChatServiceError: If deletion fails
        """
        db = get_db_session()
        try:
            repo = DocumentRepository(db)
            chunk_repo = ChunkRepository(db)
            document = repo.get_by_id(document_id)
            
            if not document:
                raise ChatServiceError(f"Document not found: {document_id}")

            if settings.QDRANT_ENABLED:
                try:
                    qdrant_client = get_qdrant_client()
                    if qdrant_client.is_available():
                        qdrant_client.delete_vectors(document_id)
                except Exception as e:
                    logger.error(
                        f"Failed to delete document vectors: {str(e)}",
                        extra={"document_id": document_id},
                    )
            
            chunk_repo.delete_by_document(document_id)
            db.delete(document)
            db.commit()
            
            logger.info(
                f"Document deleted",
                extra={"document_id": document_id}
            )
            
        except ChatServiceError:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting document: {str(e)}")
            raise ChatServiceError(f"Failed to delete document: {str(e)}")
        finally:
            db.close()

    def get_document_chunks(self, document_id: str) -> list[dict]:
        """Get stored chunks for a document."""
        db = get_db_session()
        try:
            repo = ChunkRepository(db)
            chunks = repo.get_by_document(document_id)

            return [
                {
                    "id": chunk.id,
                    "document_id": chunk.document_id,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "tokens": chunk.tokens,
                    "created_at": chunk.created_at.isoformat() if chunk.created_at else None,
                }
                for chunk in chunks
            ]

        except Exception as e:
            logger.error(f"Error getting document chunks: {str(e)}")
            raise ChatServiceError(f"Failed to get document chunks: {str(e)}")
        finally:
            db.close()
