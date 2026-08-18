# Qdrant Vector Database Setup for Melo-AI

Qdrant is a vector database used for semantic search and RAG (Retrieval Augmented Generation) in Melo-AI. It stores embeddings of document chunks for intelligent document retrieval.

---

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Getting Started](#getting-started)
5. [Usage](#usage)
6. [API Endpoints](#api-endpoints)
7. [Troubleshooting](#troubleshooting)

---

## Overview

### What is Qdrant?

Qdrant is a vector similarity search engine that:
- Stores high-dimensional vectors (embeddings)
- Performs fast similarity search
- Enables semantic search on documents
- Supports filtering and payload metadata

### Architecture Flow

```
Document Upload
    ↓
Text Chunking
    ↓
Generate Embeddings (SentenceTransformers)
    ↓
Store in Qdrant
    ↓
Query → Search in Qdrant → Return Similar Chunks
```

### Key Components

1. **Qdrant Server** - Vector database backend
2. **Embedding Model** - SentenceTransformers (all-MiniLM-L6-v2)
3. **Vector Client** - Connection manager
4. **Embedding Service** - Text to vector conversion

---

## Installation

### Step 1: Install Dependencies

Dependencies are already added to `requirements.txt`:

```bash
cd backend
pip install -r requirements.txt
```

**Key packages:**
- `qdrant-client==1.10.1` - Qdrant Python client
- `sentence-transformers==3.0.1` - Embedding generation
- `torch==2.3.1` - Deep learning framework

### Step 2: Install Qdrant Server

#### Option A: Docker (Recommended)

**Windows (PowerShell):**
```powershell
docker run -p 6333:6333 -p 6334:6334 `
  -v qdrant_storage:/qdrant/storage:z `
  qdrant/qdrant:latest
```

**macOS/Linux:**
```bash
docker run -p 6333:6333 -p 6334:6334 \
  -v qdrant_storage:/qdrant/storage:z \
  qdrant/qdrant:latest
```

#### Option B: Direct Installation

**macOS:**
```bash
brew install qdrant
qdrant
```

**Linux (Ubuntu/Debian):**
```bash
wget https://github.com/qdrant/qdrant/releases/download/v1.10.1/qdrant-x86_64-unknown-linux-gnu.zip
unzip qdrant-x86_64-unknown-linux-gnu.zip
./qdrant
```

**Windows:**
1. Download from: https://github.com/qdrant/qdrant/releases
2. Extract the executable
3. Run: `qdrant.exe`

#### Option C: Qdrant Cloud (Production)

1. Go to https://cloud.qdrant.io
2. Create account and cluster
3. Get API key and URL
4. Use in configuration

### Step 3: Verify Installation

```bash
curl http://localhost:6333/health
```

Expected response:
```json
{"title":"qdrant - vector search engine"}
```

---

## Configuration

### Environment Variables

Update `backend/.env` with:

```env
# Qdrant Server Configuration
QDRANT_URL=http://localhost:6333              # Local or cloud URL
QDRANT_API_KEY=                               # Leave empty for local, add for cloud
QDRANT_COLLECTION_NAME=melo_documents         # Collection name
QDRANT_VECTOR_SIZE=384                        # Embedding dimension (all-MiniLM-L6-v2)
QDRANT_TIMEOUT=30                             # Request timeout (seconds)
QDRANT_ENABLED=true                           # Enable/disable Qdrant

# Embedding Configuration
EMBEDDING_MODEL=all-MiniLM-L6-v2             # HuggingFace model
EMBEDDING_DEVICE=cpu                          # 'cpu' or 'cuda' (GPU)
```

### Available Embedding Models

| Model | Dimension | Speed | Quality | Size |
|-------|-----------|-------|---------|------|
| all-MiniLM-L6-v2 | 384 | ⭐⭐⭐ | ⭐⭐ | 22MB |
| all-mpnet-base-v2 | 768 | ⭐⭐ | ⭐⭐⭐ | 109MB |
| paraphrase-MiniLM-L6-v2 | 384 | ⭐⭐⭐ | ⭐⭐ | 22MB |
| multilingual-e5-small | 384 | ⭐⭐⭐ | ⭐⭐⭐ | 33MB |

**Recommendation:** Start with `all-MiniLM-L6-v2` (fast, small, good quality)

---

## Getting Started

### Step 1: Start Qdrant Server

**Using Docker:**
```powershell
docker run -p 6333:6333 -p 6334:6334 -v qdrant_storage:/qdrant/storage:z qdrant/qdrant:latest
```

**Using Local Installation:**
```bash
cd path/to/qdrant
./qdrant
```

### Step 2: Start Melo-AI Backend

```bash
cd backend
python -m uvicorn main:app --reload
```

### Step 3: Initialize Collection

The collection is automatically created on first use. Verify with:

```bash
curl http://localhost:8000/health
```

Look for Qdrant status in response.

---

## Usage

### 1. Upload Document

**Request:**
```bash
curl -X POST http://localhost:8000/documents \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "example.txt",
    "file_type": "txt",
    "content": "Your document content here...",
    "session_id": "optional-session-uuid"
  }'
```

**Response:**
```json
{
  "id": "doc-uuid",
  "filename": "example.txt",
  "file_type": "txt",
  "chunk_count": 5,
  "created_at": "2026-08-19T10:30:00Z"
}
```

**Behind the scenes:**
- Text is split into chunks (1000 chars, 150 overlap)
- Each chunk is embedded using SentenceTransformers
- Embeddings are stored in Qdrant with metadata

### 2. Search Similar Documents

**Request:**
```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is artificial intelligence?",
    "limit": 5,
    "threshold": 0.7
  }'
```

**Response:**
```json
{
  "results": [
    {
      "document_id": "doc-uuid",
      "chunk_index": 2,
      "content": "AI is a field of...",
      "similarity_score": 0.85,
      "metadata": {...}
    }
  ]
}
```

### 3. Use in Chat with RAG

In chat context:
1. User sends a question
2. Embed the question
3. Search Qdrant for similar document chunks
4. Include results in chat context
5. AI responds with knowledge from documents

**Pseudo-code:**
```python
# In chat_service.py
query_embedding = embedding_service.embed_query(user_message)
relevant_docs = qdrant_client.search(query_embedding, limit=3)
context = "\n".join([doc['content'] for doc in relevant_docs])
prompt = f"Context:\n{context}\n\nQuestion: {user_message}"
response = ollama_client.generate(prompt)
```

---

## API Endpoints

### Document Management

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/documents` | POST | Upload document |
| `/documents/{id}` | GET | Get document details |
| `/sessions/{id}/documents` | GET | List session documents |
| `/documents/{id}` | DELETE | Delete document |

### Search (Future)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/search` | POST | Search documents |
| `/search/similar` | POST | Find similar chunks |

### Admin (Future)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/admin/qdrant/health` | GET | Qdrant health check |
| `/admin/qdrant/stats` | GET | Collection statistics |
| `/admin/qdrant/rebuild` | POST | Rebuild embeddings |

---

## Python API Usage

### Basic Usage

```python
from services.qdrant_client import get_qdrant_client
from services.embedding_service import get_embedding_service

# Get services
qdrant = get_qdrant_client()
embedder = get_embedding_service()

# Create collection
qdrant.create_collection()

# Generate embedding
text = "Hello world"
embedding = embedder.embed_text(text)

# Store vector
qdrant.upsert_vector(
    document_id="doc-123",
    chunk_index=0,
    embedding=embedding,
    payload={"content": text, "source": "example"}
)

# Search
query = "Hi there"
query_embedding = embedder.embed_query(query)
results = qdrant.search(query_embedding, limit=5)

for result in results:
    print(f"Score: {result['similarity_score']}, Content: {result['content']}")
```

### Batch Operations

```python
# Embed multiple texts
texts = ["Document 1", "Document 2", "Document 3"]
embeddings = embedder.embed_texts(texts)

# Store multiple vectors
for i, embedding in enumerate(embeddings):
    qdrant.upsert_vector(
        document_id="doc-123",
        chunk_index=i,
        embedding=embedding,
        payload={"content": texts[i]}
    )

# Delete all vectors for a document
qdrant.delete_vectors("doc-123")
```

### Health Checks

```python
# Check Qdrant availability
if qdrant.is_available():
    info = qdrant.get_collection_info()
    print(f"Collection has {info['points_count']} vectors")
else:
    print("Qdrant is not available")

# Get health status
status = qdrant.health_check()
print(status)
```

---

## Troubleshooting

### Issue: Connection Refused

**Problem:** Cannot connect to Qdrant
```
Error: Connection refused: http://localhost:6333
```

**Solution:**
1. Check if Qdrant is running
2. Verify URL in .env: `QDRANT_URL=http://localhost:6333`
3. Check firewall (port 6333)
4. If using Docker: `docker ps` to see if container is running

### Issue: Model Download Slow

**Problem:** First embedding generation is very slow (downloading model)
```
Downloading model: all-MiniLM-L6-v2
```

**Solution:**
1. First use downloads ~22MB (one-time)
2. Consider pre-downloading during setup
3. For production, cache the model

**Pre-download:**
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
# This downloads and caches the model
```

### Issue: CUDA Out of Memory

**Problem:** GPU out of memory when generating embeddings
```
RuntimeError: CUDA out of memory
```

**Solution:**
1. Change to CPU: `EMBEDDING_DEVICE=cpu`
2. Or use smaller model: `EMBEDDING_MODEL=all-MiniLM-L6-v2`
3. Batch fewer texts at once

### Issue: Collection Not Found

**Problem:** Collection doesn't exist when trying to search
```
Status.NOT_FOUND: Collection `melo_documents` does not exist
```

**Solution:**
```python
from services.qdrant_client import get_qdrant_client
client = get_qdrant_client()
client.create_collection(force_recreate=False)
```

### Issue: Embedding Dimension Mismatch

**Problem:** Error about vector size mismatch
```
Status.BAD_REQUEST: Wrong vector dimension 768, expected 384
```

**Solution:**
1. Check EMBEDDING_MODEL matches QDRANT_VECTOR_SIZE:
   - all-MiniLM-L6-v2 → 384
   - all-mpnet-base-v2 → 768
2. Recreate collection with correct dimension:
   ```python
   qdrant.create_collection(force_recreate=True)
   ```

---

## Performance Tuning

### Indexing

By default, Qdrant uses HNSW (Hierarchical Navigable Small World) for fast approximate search.

```python
# For large collections, configure indexing
qdrant.client.create_collection(
    collection_name="melo_documents",
    vectors_config=models.VectorParams(
        size=384,
        distance=models.Distance.COSINE
    ),
    hnsw_config=models.HnswConfigDiff(
        m=16,
        ef_construct=200,
        max_payload_size=30_000_000
    )
)
```

### Batch Operations

For bulk upload, batch operations are more efficient:

```python
points = [
    models.PointStruct(
        id=i,
        vector=embeddings[i],
        payload={"content": texts[i]}
    )
    for i in range(len(texts))
]

qdrant.client.upsert(
    collection_name="melo_documents",
    points=points
)
```

### Query Optimization

Use filters to reduce search space:

```python
results = qdrant.search(
    query_embedding=embedding,
    filters={"document_id": "specific-doc"},
    limit=10
)
```

---

## Next Steps

1. ✅ Install Qdrant server
2. ✅ Configure `.env` with Qdrant settings
3. ✅ Test connection: `curl http://localhost:6333/health`
4. ✅ Start backend: `python -m uvicorn main:app --reload`
5. Upload a test document via API
6. Implement RAG in chat service
7. Add search endpoints
8. Test end-to-end document search

---

## References

- **Qdrant Docs:** https://qdrant.tech/documentation/
- **SentenceTransformers:** https://www.sbert.net/
- **HuggingFace Models:** https://huggingface.co/sentence-transformers
- **Vector Databases:** https://en.wikipedia.org/wiki/Vector_database
