"""Quick test script for Qdrant setup"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from services.qdrant_client import get_qdrant_client
from services.embedding_service import get_embedding_service


def test_qdrant_connection():
    """Test Qdrant server connection"""
    print("\n=== Testing Qdrant Connection ===")
    qdrant = get_qdrant_client()
    
    if qdrant.is_available():
        print("✓ Qdrant server is available")
        return True
    else:
        print("✗ Qdrant server is NOT available")
        print("  Make sure Qdrant is running on:", qdrant.url)
        return False


def test_collection_creation():
    """Test collection creation"""
    print("\n=== Testing Collection Creation ===")
    qdrant = get_qdrant_client()
    
    try:
        # Create collection
        qdrant.create_collection(force_recreate=False)
        print("✓ Collection created or already exists")
        
        # Get collection info
        info = qdrant.get_collection_info()
        print(f"  Collection: {info.get('name')}")
        print(f"  Points: {info.get('points_count')}")
        return True
        
    except Exception as e:
        print(f"✗ Collection creation failed: {str(e)}")
        return False


def test_embedding_service():
    """Test embedding service"""
    print("\n=== Testing Embedding Service ===")
    
    try:
        embedder = get_embedding_service()
        print("✓ Embedding service initialized")
        
        # Get model info
        info = embedder.model_info()
        print(f"  Model: {info['model_name']}")
        print(f"  Dimension: {info['embedding_dimension']}")
        print(f"  Device: {info['device']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Embedding service failed: {str(e)}")
        print("  Make sure you have internet connection to download the model")
        return False


def test_embedding_generation():
    """Test single text embedding"""
    print("\n=== Testing Embedding Generation ===")
    
    try:
        embedder = get_embedding_service()
        
        # Embed a test text
        text = "Melo-AI is a local-first AI assistant"
        embedding = embedder.embed_text(text)
        
        print(f"✓ Text embedded successfully")
        print(f"  Text: {text}")
        print(f"  Embedding dimension: {len(embedding)}")
        print(f"  Sample values: {embedding[:3]}")
        
        return True, embedding
        
    except Exception as e:
        print(f"✗ Embedding generation failed: {str(e)}")
        return False, None


def test_batch_embedding():
    """Test batch text embedding"""
    print("\n=== Testing Batch Embedding ===")
    
    try:
        embedder = get_embedding_service()
        
        texts = [
            "First document about AI",
            "Second document about machine learning",
            "Third document about neural networks"
        ]
        
        embeddings = embedder.embed_texts(texts)
        
        print(f"✓ Batch embedded {len(embeddings)} texts")
        print(f"  Embedding dimension: {len(embeddings[0])}")
        
        return True, embeddings
        
    except Exception as e:
        print(f"✗ Batch embedding failed: {str(e)}")
        return False, None


def test_vector_upsert():
    """Test storing vector in Qdrant"""
    print("\n=== Testing Vector Upsert ===")
    
    try:
        qdrant = get_qdrant_client()
        embedder = get_embedding_service()
        
        # Generate embedding
        text = "Test document for Qdrant storage"
        embedding = embedder.embed_text(text)
        
        # Store vector
        doc_id = "test-doc-001"
        chunk_index = 0
        
        qdrant.upsert_vector(
            document_id=doc_id,
            chunk_index=chunk_index,
            embedding=embedding,
            payload={"content": text, "source": "test"}
        )
        
        print(f"✓ Vector stored successfully")
        print(f"  Document ID: {doc_id}")
        print(f"  Chunk Index: {chunk_index}")
        
        return True, doc_id
        
    except Exception as e:
        print(f"✗ Vector upsert failed: {str(e)}")
        return False, None


def test_vector_search():
    """Test searching vectors"""
    print("\n=== Testing Vector Search ===")
    
    try:
        qdrant = get_qdrant_client()
        embedder = get_embedding_service()
        
        # Generate query embedding
        query = "AI and machine learning"
        query_embedding = embedder.embed_query(query)
        
        # Search
        results = qdrant.search(
            query_embedding=query_embedding,
            limit=5,
            score_threshold=0.0
        )
        
        print(f"✓ Search completed")
        print(f"  Query: {query}")
        print(f"  Results found: {len(results)}")
        
        for i, result in enumerate(results, 1):
            print(f"  [{i}] Score: {result['similarity_score']:.3f}, "
                  f"Doc: {result['document_id']}, "
                  f"Chunk: {result['chunk_index']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Vector search failed: {str(e)}")
        return False


def test_vector_deletion():
    """Test deleting vectors"""
    print("\n=== Testing Vector Deletion ===")
    
    try:
        qdrant = get_qdrant_client()
        
        doc_id = "test-doc-001"
        qdrant.delete_vectors(doc_id)
        
        print(f"✓ Vectors deleted")
        print(f"  Document ID: {doc_id}")
        
        return True
        
    except Exception as e:
        print(f"✗ Vector deletion failed: {str(e)}")
        return False


def test_health_check():
    """Test health check endpoint"""
    print("\n=== Testing Health Check ===")
    
    try:
        qdrant = get_qdrant_client()
        health = qdrant.health_check()
        
        print(f"✓ Health check completed")
        print(f"  Status: {health.get('status')}")
        
        if health.get('status') == 'healthy':
            info = health.get('collection_info', {})
            print(f"  Collection: {info.get('name')}")
            print(f"  Points: {info.get('points_count')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Health check failed: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*50)
    print("QDRANT SETUP VERIFICATION")
    print("="*50)
    
    tests = [
        ("Qdrant Connection", test_qdrant_connection),
        ("Collection Creation", test_collection_creation),
        ("Embedding Service", test_embedding_service),
        ("Embedding Generation", test_embedding_generation),
        ("Batch Embedding", test_batch_embedding),
        ("Vector Upsert", test_vector_upsert),
        ("Vector Search", test_vector_search),
        ("Vector Deletion", test_vector_deletion),
        ("Health Check", test_health_check),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            # Handle tuple returns
            if isinstance(result, tuple):
                results.append((test_name, result[0]))
            else:
                results.append((test_name, result))
        except Exception as e:
            print(f"✗ Test error: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} - {test_name}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed! Qdrant is ready to use.")
    else:
        print("\n✗ Some tests failed. See above for details.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)