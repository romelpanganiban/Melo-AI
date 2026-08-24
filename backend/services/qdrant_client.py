"""Qdrant Vector Database Client for Melo-AI"""

from typing import List, Optional, Dict, Any
from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse
import uuid

from core.logging import logger
from core.errors import ChatServiceError
from core.settings import settings


class QdrantVectorClient:
    """Client for interacting with Qdrant vector database"""
    
    def __init__(
        self,
        url: str = None,
        api_key: str = None,
        collection_name: str = None,
        vector_size: int = None,
        timeout: int = None
    ):
        """Initialize Qdrant client
        
        Args:
            url: Qdrant server URL (default: from settings)
            api_key: API key for Qdrant (optional)
            collection_name: Collection name (default: from settings)
            vector_size: Vector embedding size (default: from settings)
            timeout: Request timeout in seconds
        """
        self.url = url or settings.QDRANT_URL
        self.api_key = api_key or settings.QDRANT_API_KEY
        self.collection_name = collection_name or settings.QDRANT_COLLECTION_NAME
        self.vector_size = vector_size or settings.QDRANT_VECTOR_SIZE
        self.timeout = timeout or settings.QDRANT_TIMEOUT
        
        try:
            # Initialize Qdrant client
            self.client = QdrantClient(
                url=self.url,
                api_key=self.api_key,
                timeout=self.timeout
            )
            logger.info(
                f"Qdrant client initialized",
                extra={
                    "url": self.url,
                    "collection": self.collection_name,
                    "vector_size": self.vector_size
                }
            )
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {str(e)}")
            raise ChatServiceError(f"Qdrant initialization failed: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if Qdrant server is available
        
        Returns:
            True if server is running, False otherwise
        """
        try:
            self.client.get_collections()
            return True
        except Exception as e:
            logger.warning(f"Qdrant server not available: {str(e)}")
            return False
    
    def create_collection(self, force_recreate: bool = False) -> bool:
        """Create or verify collection exists
        
        Args:
            force_recreate: If True, delete and recreate the collection
            
        Returns:
            True if collection was created or already exists
            
        Raises:
            ChatServiceError: If collection creation fails
        """
        try:
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if self.collection_name in collection_names:
                if force_recreate:
                    logger.info(f"Deleting collection: {self.collection_name}")
                    self.client.delete_collection(self.collection_name)
                else:
                    logger.info(f"Collection already exists: {self.collection_name}")
                    return True
            
            # Create new collection with vector configuration
            logger.info(f"Creating collection: {self.collection_name}")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.vector_size,
                    distance=models.Distance.COSINE
                ),
                # Keep collection options compatible with current Qdrant clients.
                optimizers_config=models.OptimizersConfigDiff(
                    default_segment_number=5
                )
            )
            
            logger.info(f"Collection created successfully: {self.collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create collection: {str(e)}")
            raise ChatServiceError(f"Collection creation failed: {str(e)}")
    
    def upsert_vector(
        self,
        document_id: str,
        chunk_index: int,
        embedding: List[float],
        payload: Dict[str, Any]
    ) -> bool:
        """Add or update a vector in the collection
        
        Args:
            document_id: Document ID
            chunk_index: Chunk index
            embedding: Vector embedding (list of floats)
            payload: Additional metadata to store
            
        Returns:
            True if successful
            
        Raises:
            ChatServiceError: If upsert fails
        """
        try:
            # Create point ID from document_id and chunk_index
            point_id = int(
                uuid.uuid5(
                    uuid.NAMESPACE_DNS,
                    f"{document_id}_{chunk_index}"
                ).int % (2**63 - 1)
            )
            
            # Prepare point data
            point = models.PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "document_id": document_id,
                    "chunk_index": chunk_index,
                    **payload
                }
            )
            
            # Upsert to collection
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            logger.debug(f"Vector upserted: {point_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upsert vector: {str(e)}")
            raise ChatServiceError(f"Vector upsert failed: {str(e)}")
    
    def search(
        self,
        query_embedding: List[float],
        limit: int = 5,
        score_threshold: float = 0.5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors
        
        Args:
            query_embedding: Query vector embedding
            limit: Maximum number of results
            score_threshold: Minimum similarity score (0-1)
            filters: Optional filters for payload
            
        Returns:
            List of search results with metadata
            
        Raises:
            ChatServiceError: If search fails
        """
        try:
            # Build query filter if provided
            query_filter = None
            if filters:
                # Convert filters dict to Qdrant filter format
                conditions = []
                for key, value in filters.items():
                    conditions.append(
                        models.HasIdCondition(has_id=[value])
                        if key == "document_id"
                        else models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value)
                        )
                    )
                query_filter = models.Filter(must=conditions) if conditions else None
            
            # Search in collection
            if hasattr(self.client, "query_points"):
                query_response = self.client.query_points(
                    collection_name=self.collection_name,
                    query=query_embedding,
                    limit=limit,
                    score_threshold=score_threshold,
                    query_filter=query_filter,
                )
                search_results = getattr(query_response, "points", query_response)
            else:
                search_results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_embedding,
                    limit=limit,
                    score_threshold=score_threshold,
                    query_filter=query_filter,
                )
            
            # Format results
            results = []
            for point in search_results:
                results.append({
                    "document_id": point.payload.get("document_id"),
                    "chunk_index": point.payload.get("chunk_index"),
                    "content": point.payload.get("content"),
                    "similarity_score": point.score,
                    "metadata": point.payload
                })
            
            logger.debug(f"Search completed: {len(results)} results found")
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise ChatServiceError(f"Search failed: {str(e)}")
    
    def delete_vectors(self, document_id: str) -> bool:
        """Delete all vectors for a document
        
        Args:
            document_id: Document ID
            
        Returns:
            True if successful
            
        Raises:
            ChatServiceError: If deletion fails
        """
        try:
            # Delete points by payload filter
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="document_id",
                                match=models.MatchValue(value=document_id)
                            )
                        ]
                    )
                )
            )
            
            logger.info(f"Vectors deleted for document: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete vectors: {str(e)}")
            raise ChatServiceError(f"Vector deletion failed: {str(e)}")
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection information
        
        Returns:
            Dictionary with collection metadata
        """
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": getattr(info, "name", self.collection_name),
                "points_count": getattr(info, "points_count", 0),
                "config": getattr(info, "config", None),
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {str(e)}")
            return {"error": str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on Qdrant server
        
        Returns:
            Health status information
        """
        try:
            if self.is_available():
                collection_info = self.get_collection_info()
                return {
                    "status": "healthy",
                    "server_url": self.url,
                    "collection": self.collection_name,
                    "collection_info": collection_info
                }
            else:
                return {
                    "status": "unavailable",
                    "error": "Cannot connect to Qdrant server"
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }


# Global Qdrant client instance
_qdrant_client = None


def get_qdrant_client() -> QdrantVectorClient:
    """Get or create Qdrant client singleton
    
    Returns:
        QdrantVectorClient instance
    """
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantVectorClient()
    return _qdrant_client
