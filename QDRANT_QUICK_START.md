# Qdrant Setup - Quick Start Guide

Complete setup instructions for Qdrant vector database in Melo-AI.

---

## Prerequisites Checklist

- [ ] Python 3.9+ installed
- [ ] Backend dependencies installed (`pip install -r requirements.txt`)
- [ ] Docker installed (optional, for Qdrant container)
- [ ] Internet connection (for downloading models)

---

## Quick Setup (5 minutes)

### 1. Update Dependencies ✅

```bash
cd backend
pip install -r requirements.txt
```

**Installed packages:**
- `qdrant-client==1.10.1` - Vector database client
- `sentence-transformers==3.0.1` - Embedding generation
- `torch==2.3.1` - Deep learning framework

### 2. Start Qdrant Server

**Option A: Docker (Recommended)**

```powershell
# Windows PowerShell
docker run -p 6333:6333 -p 6334:6334 `
  -v qdrant_storage:/qdrant/storage:z `
  qdrant/qdrant:latest
```

**Option B: Direct Installation**

Download from: https://github.com/qdrant/qdrant/releases

### 3. Verify Qdrant is Running

```bash
curl http://localhost:6333/health
```

Expected: `{"title":"qdrant - vector search engine"}`

### 4. Test Setup

```bash
cd backend
python test_qdrant.py
```

Expected output:
```
==================================================
QDRANT SETUP VERIFICATION
==================================================

=== Testing Qdrant Connection ===
✓ Qdrant server is available

=== Testing Embedding Service ===
✓ Embedding service initialized
  Model: all-MiniLM-L6-v2
  Dimension: 384
  Device: cpu

=== Testing Vector Upsert ===
✓ Vector stored successfully

=== Testing Vector Search ===
✓ Search completed
  Results found: 1

==================================================
TEST SUMMARY
==================================================

✓ PASS - Qdrant Connection
✓ PASS - Collection Creation
✓ PASS - Embedding Service
✓ PASS - Embedding Generation
✓ PASS - Batch Embedding
✓ PASS - Vector Upsert
✓ PASS - Vector Search
✓ PASS - Vector Deletion
✓ PASS - Health Check

Passed: 9/9

✓ All tests passed! Qdrant is ready to use.
```

---

## Configuration

### Environment Variables (`.env`)

```env
# Qdrant Configuration
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=                           # Leave empty for local
QDRANT_COLLECTION_NAME=melo_documents
QDRANT_VECTOR_SIZE=384
QDRANT_TIMEOUT=30
QDRANT_ENABLED=true

# Embeddings Configuration
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu                      # Change to 'cuda' for GPU
```

---

## Usage Examples

### Python API

```python
# Import services
from services.qdrant_client import get_qdrant_client
from services.embedding_service import get_embedding_service

# Get clients
qdrant = get_qdrant_client()
embedder = get_embedding_service()

# Create collection
qdrant.create_collection()

# Embed text
text = "Melo-AI is a local-first AI assistant"
embedding = embedder.embed_text(text)

# Store vector
qdrant.upsert_vector(
    document_id="doc-123",
    chunk_index=0,
    embedding=embedding,
    payload={"content": text}
)

# Search
query = "What is AI?"
query_embedding = embedder.embed_query(query)
results = qdrant.search(query_embedding, limit=5)

for result in results:
    print(f"Score: {result['similarity_score']:.2f}")
    print(f"Content: {result['content']}")
```

### HTTP API

```bash
# Upload document
curl -X POST http://localhost:8000/documents \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "guide.txt",
    "file_type": "txt",
    "content": "Your document content here...",
    "session_id": "optional-uuid"
  }'

# Response:
{
  "id": "doc-uuid",
  "filename": "guide.txt",
  "chunk_count": 5,
  "created_at": "2026-08-19T10:30:00Z"
}
```

---

## Files Created/Modified

### New Files

| File | Purpose |
|------|---------|
| `services/qdrant_client.py` | Qdrant connection and operations |
| `services/embedding_service.py` | Text embedding generation |
| `tests/test_qdrant_client.py` | Unit tests for Qdrant |
| `tests/test_embedding_service.py` | Unit tests for embeddings |
| `test_qdrant.py` | Integration test script |
| `QDRANT_SETUP.md` | Detailed setup documentation |
| `RAG_INTEGRATION_GUIDE.md` | RAG implementation guide |

### Modified Files

| File | Change |
|------|--------|
| `requirements.txt` | Added Qdrant, SentenceTransformers, Torch |
| `.env.example` | Added Qdrant configuration variables |
| `core/settings.py` | Added Qdrant and embedding settings |

---

## Architecture

```
Frontend (Next.js)
    ↓
Backend (FastAPI)
    ├─→ Chat API
    │   └─→ Chat Service
    │       ├─→ Embedding Service (SentenceTransformers)
    │       ├─→ Qdrant Client (Vector Search)
    │       └─→ Ollama Client (LLM)
    │
    ├─→ Document API
    │   └─→ Document Service
    │       ├─→ Text Chunking
    │       ├─→ Embedding Service
    │       └─→ Qdrant Client (Storage)
    │
    └─→ Health API
        └─→ Qdrant Health Check
```

---

## Running Tests

### Quick Test Script

```bash
cd backend
python test_qdrant.py
```

### Pytest Unit Tests

```bash
cd backend

# Test Qdrant client
pytest tests/test_qdrant_client.py -v

# Test embedding service
pytest tests/test_embedding_service.py -v

# Run all tests
pytest tests/ -v
```

### Integration Test

```bash
# 1. Start all services
docker run -p 6333:6333 qdrant/qdrant  # Terminal 1
cd backend
python -m uvicorn main:app --reload     # Terminal 2

# 2. Test in another terminal
python test_qdrant.py

# 3. Test with API
curl -X GET http://localhost:8000/health
```

---

## Troubleshooting

### Connection Refused

```bash
# Check if Qdrant is running
docker ps  # Should show qdrant container

# If not running, start it:
docker run -p 6333:6333 qdrant/qdrant:latest
```

### Model Download Slow

First embedding generation downloads ~22MB model (one-time):

```python
# Pre-download during setup
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
print("Model cached!")
```

### CUDA Out of Memory

```env
# Switch to CPU in .env
EMBEDDING_DEVICE=cpu
```

### Collection Not Found

```python
from services.qdrant_client import get_qdrant_client
client = get_qdrant_client()
client.create_collection()  # Create if doesn't exist
```

---

## Performance Tips

### For Speed
- Use `all-MiniLM-L6-v2` (default)
- Set `EMBEDDING_DEVICE=cpu`
- Limit search results to 3-5
- Increase score threshold to 0.75

### For Quality
- Use `all-mpnet-base-v2`
- Set `EMBEDDING_DEVICE=cuda` (if available)
- Reduce score threshold to 0.5-0.6
- Increase search results to 5-10

---

## Next Steps

1. ✅ Install Qdrant
2. ✅ Configure environment
3. ✅ Run tests
4. [ ] Upload sample documents
5. [ ] Test document search
6. [ ] Implement RAG in chat service
7. [ ] Add search endpoint
8. [ ] Integrate with frontend

---

## Documentation

- **Detailed Setup**: See [QDRANT_SETUP.md](QDRANT_SETUP.md)
- **RAG Guide**: See [RAG_INTEGRATION_GUIDE.md](RAG_INTEGRATION_GUIDE.md)
- **API Reference**: See [ARCHITECTURE.md](ARCHITECTURE.md)

---

## Support

### Check Status

```bash
# Qdrant health
curl http://localhost:6333/health

# Backend health
curl http://localhost:8000/health

# Verify setup
python test_qdrant.py
```

### View Logs

```bash
# Backend logs
tail -f backend/logs/melo.log

# Qdrant logs (Docker)
docker logs <container-id>
```

### Debug

```python
# Test embedding
from services.embedding_service import get_embedding_service
embedder = get_embedding_service()
embedding = embedder.embed_text("test")
print(f"Embedding dim: {len(embedding)}")

# Test Qdrant
from services.qdrant_client import get_qdrant_client
qdrant = get_qdrant_client()
print(qdrant.health_check())
```

---

## Success Criteria

✅ Qdrant server is running
✅ Collection is created
✅ Embeddings generate successfully
✅ Vectors store in Qdrant
✅ Similarity search works
✅ All tests pass

If all criteria are met, Qdrant is ready for production use!

---

**Setup Time**: ~5 minutes  
**Last Updated**: 2026-08-19
