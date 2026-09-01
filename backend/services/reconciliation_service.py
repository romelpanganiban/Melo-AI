"""Service for reconciling SQL documents with Qdrant vector embeddings."""

from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from core.logging import logger
from core.errors import ChatServiceError
from core.settings import settings
from database import DocumentRepository, ChunkRepository, get_db_session
from services.embedding_service import get_embedding_service
from services.qdrant_client import get_qdrant_client


class ReconciliationReport:
    """Report of reconciliation findings and actions."""
    
    def __init__(self):
        self.timestamp = datetime.now(timezone.utc)
        self.sql_documents = 0
        self.qdrant_vectors = 0
        self.missing_embeddings = []  # Documents in SQL missing from Qdrant
        self.orphaned_embeddings = []  # Document IDs in Qdrant missing from SQL
        self.repaired_count = 0
        self.deleted_count = 0
        self.errors = []
    
    def to_dict(self) -> dict:
        """Convert report to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "summary": {
                "sql_documents": self.sql_documents,
                "qdrant_vectors": self.qdrant_vectors,
                "missing_embeddings": len(self.missing_embeddings),
                "orphaned_embeddings": len(self.orphaned_embeddings),
                "repaired": self.repaired_count,
                "deleted": self.deleted_count,
                "errors": len(self.errors),
            },
            "missing_embeddings": self.missing_embeddings,
            "orphaned_embeddings": self.orphaned_embeddings,
            "errors": self.errors,
        }


class ReconciliationService:
    """Service for reconciling SQL and Qdrant data consistency."""
    
    def __init__(self):
        self.report = ReconciliationReport()
    
    def audit(self) -> ReconciliationReport:
        """Audit SQL and Qdrant for inconsistencies without making changes.
        
        Returns:
            ReconciliationReport with findings
        """
        logger.info("Starting Qdrant/SQL reconciliation audit")
        self.report = ReconciliationReport()
        
        try:
            # Get all documents from SQL
            db = get_db_session()
            try:
                # Query all documents directly from the database
                from database.models import Document
                sql_documents = db.query(Document).all()
                self.report.sql_documents = len(sql_documents)
                logger.info(f"Found {len(sql_documents)} documents in SQL")
                
                # Get document IDs from SQL
                sql_doc_ids = {doc.id for doc in sql_documents}
                
                # Get vectors from Qdrant
                if not settings.QDRANT_ENABLED:
                    logger.warning("Qdrant is disabled; skipping vector audit")
                    self.report.errors.append("Qdrant is disabled")
                    return self.report
                
                qdrant_client = get_qdrant_client()
                
                # Retrieve all vectors to check consistency
                # Using scroll with limit to avoid memory issues
                vectors_scanned = set()
                batch_size = 100
                
                try:
                    # Get collection info to understand size
                    info = qdrant_client.get_collection_info()
                    vector_count = info.get("count", 0) if isinstance(info, dict) else 0
                    self.report.qdrant_vectors = vector_count
                    logger.info(f"Found {vector_count} vectors in Qdrant")
                    
                    # Scroll through vectors to find orphaned ones
                    points, _ = qdrant_client.client.scroll(
                        collection_name=qdrant_client.collection_name,
                        limit=batch_size,
                        with_payload=True,
                        with_vectors=False
                    )
                    
                    while points:
                        for point in points:
                            doc_id = point.payload.get("document_id")
                            if doc_id:
                                vectors_scanned.add(doc_id)
                                if doc_id not in sql_doc_ids:
                                    self.report.orphaned_embeddings.append(doc_id)
                        
                        # Get next batch
                        points, _ = qdrant_client.client.scroll(
                            collection_name=qdrant_client.collection_name,
                            limit=batch_size,
                            offset=len(vectors_scanned),
                            with_payload=True,
                            with_vectors=False
                        )
                
                except Exception as e:
                    logger.error(f"Failed to scan Qdrant vectors: {str(e)}")
                    self.report.errors.append(f"Failed to scan Qdrant: {str(e)}")
                
                # Find documents missing embeddings
                for doc in sql_documents:
                    # A document is considered missing embeddings if:
                    # 1. It has chunks but no corresponding vector was found in our scan
                    # Note: We simplify by checking if doc_id appears in scanned vectors
                    if doc.chunk_count > 0 and doc.id not in vectors_scanned:
                        self.report.missing_embeddings.append({
                            "document_id": doc.id,
                            "filename": doc.filename,
                            "chunk_count": doc.chunk_count,
                            "workspace_id": doc.workspace_id,
                        })
                
                # Remove duplicates from orphaned list
                self.report.orphaned_embeddings = list(set(self.report.orphaned_embeddings))
                
            finally:
                db.close()
            
        except Exception as e:
            logger.error(f"Reconciliation audit failed: {str(e)}")
            self.report.errors.append(f"Audit failed: {str(e)}")
        
        return self.report
    
    def repair(self, missing_embeddings: bool = True, delete_orphaned: bool = False) -> ReconciliationReport:
        """Repair inconsistencies found during audit.
        
        Args:
            missing_embeddings: If True, re-generate embeddings for documents missing them
            delete_orphaned: If True, delete orphaned vectors from Qdrant (dangerous!)
        
        Returns:
            ReconciliationReport with repair actions taken
        """
        logger.info(f"Starting Qdrant/SQL reconciliation repair (missing={missing_embeddings}, delete_orphaned={delete_orphaned})")
        
        # First run audit to find issues
        self.audit()
        
        if not settings.QDRANT_ENABLED:
            logger.warning("Qdrant is disabled; cannot repair")
            return self.report
        
        embedding_service = get_embedding_service()
        qdrant_client = get_qdrant_client()
        db = get_db_session()
        
        try:
            # Repair missing embeddings
            if missing_embeddings and self.report.missing_embeddings:
                logger.info(f"Re-embedding {len(self.report.missing_embeddings)} documents")
                doc_repo = DocumentRepository(db)
                chunk_repo = ChunkRepository(db)
                
                for missing_doc in self.report.missing_embeddings:
                    try:
                        doc_id = missing_doc["document_id"]
                        doc = doc_repo.get_by_id(doc_id)
                        
                        if not doc:
                            logger.warning(f"Document {doc_id} not found during repair")
                            continue
                        
                        # Get all chunks for this document
                        chunks = chunk_repo.get_by_document(doc_id)
                        if not chunks:
                            logger.warning(f"No chunks found for document {doc_id}")
                            continue
                        
                        # Generate embeddings
                        chunk_texts = [chunk.content for chunk in chunks]
                        embeddings = embedding_service.embed_texts(chunk_texts)
                        
                        # Store in Qdrant
                        for chunk, embedding in zip(chunks, embeddings):
                            qdrant_client.upsert_vector(
                                document_id=doc.id,
                                chunk_index=chunk.chunk_index,
                                embedding=embedding,
                                payload={
                                    "content": chunk.content,
                                    "filename": doc.filename,
                                    "file_type": doc.file_type,
                                    "session_id": doc.session_id,
                                    "owner_id": doc.owner_id,
                                    "workspace_id": doc.workspace_id,
                                    "is_shared": doc.is_shared,
                                    "chunk_index": chunk.chunk_index,
                                    "tokens": chunk.tokens or len(chunk.content.split()),
                                }
                            )
                        
                        self.report.repaired_count += 1
                        logger.info(f"Re-embedded document {doc_id} with {len(chunks)} chunks")
                        
                    except Exception as e:
                        error_msg = f"Failed to repair document {doc_id}: {str(e)}"
                        logger.error(error_msg)
                        self.report.errors.append(error_msg)
            
            # Delete orphaned embeddings (only if explicitly requested)
            if delete_orphaned and self.report.orphaned_embeddings:
                logger.warning(f"DELETING {len(self.report.orphaned_embeddings)} orphaned vector sets")
                
                for doc_id in self.report.orphaned_embeddings:
                    try:
                        qdrant_client.delete_vectors(doc_id)
                        self.report.deleted_count += 1
                        logger.info(f"Deleted orphaned vectors for {doc_id}")
                    except Exception as e:
                        error_msg = f"Failed to delete orphaned vectors for {doc_id}: {str(e)}"
                        logger.error(error_msg)
                        self.report.errors.append(error_msg)
            
        finally:
            db.close()
        
        logger.info(f"Reconciliation repair complete: repaired={self.report.repaired_count}, deleted={self.report.deleted_count}, errors={len(self.report.errors)}")
        return self.report


def get_reconciliation_service() -> ReconciliationService:
    """Get a reconciliation service instance."""
    return ReconciliationService()
