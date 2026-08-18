# RAG (Retrieval Augmented Generation) Integration Guide

This guide explains how to implement RAG (Retrieval Augmented Generation) in Melo-AI using Qdrant vector database and document embeddings.

---

## Table of Contents

1. [What is RAG?](#what-is-rag)
2. [Architecture](#architecture)
3. [Implementation Steps](#implementation-steps)
4. [Integration with Chat Service](#integration-with-chat-service)
5. [Example Implementation](#example-implementation)
6. [Testing RAG](#testing-rag)

---

## What is RAG?

**RAG (Retrieval Augmented Generation)** is a technique that enhances AI responses by:

1. **Retrieving** relevant documents/chunks from a knowledge base
2. **Augmenting** the AI prompt with retrieved context
3. **Generating** a response using the retrieved information

### Benefits

- ✅ Answers grounded in your documents
- ✅ Reduced hallucinations
- ✅ Up-to-date information from your knowledge base
- ✅ Citations and source tracking
- ✅ Domain-specific knowledge

### Flow

```
User Query
    ↓
Embed Query (SentenceTransformers)
    ↓
Search Qdrant for Similar Documents
    ↓
Retrieve Top-K Chunks
    ↓
Build Augmented Prompt with Context
    ↓
Send to Ollama
    ↓
Generate Response with Knowledge
    ↓
Return Response + Sources
```

---

## Architecture

### Components

```
┌─────────────────────────────────────────────────────┐
│             Chat API Endpoint                       │
│            POST /chat/stream                        │
└──────────────────┬──────────────────────────────────┘
                   │
                   ↓
        ┌──────────────────────────┐
        │   Chat Service           │
        │ (with RAG Logic)         │
        └──────────┬───────────────┘
                   │
        ┌──────────┴───────────┬──────────────┐
        ↓                      ↓              ↓
   ┌─────────┐        ┌──────────────┐  ┌─────────┐
   │ Embedding   │        │   Qdrant    │  │ Ollama  │
   │  Service    │        │ Vector DB   │  │  LLM    │
   └─────────┘        └──────────────┘  └─────────┘
        │                      │
        └──────────┬───────────┘
                   ↓
        Documents + Embeddings
```

### Data Flow

```python
# 1. Document Upload (One-time)
Upload Document
    → Chunk Text
    → Generate Embeddings
    → Store in Qdrant

# 2. Chat with RAG (Per Query)
User Question
    → Embed Question
    → Search Qdrant
    → Get Top-K Chunks
    → Build Context
    → Send to Ollama
    → Return Response
```

---

## Implementation Steps

### Step 1: Update Document Service

The document service should:
1. Chunk documents
2. Generate embeddings for chunks
3. Store embeddings in Qdrant

**File: `services/document_service.py`**

```python
from services.embedding_service import get_embedding_service
from services.qdrant_client import get_qdrant_client

class DocumentService:
    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.qdrant_client = get_qdrant_client()
    
    def upload_document_with_embeddings(self, document_id, filename, content, session_id=None):
        """Upload document and generate embeddings"""
        
        # 1. Chunk the document
        chunks = self.chunk_text(content)
        
        # 2. Generate embeddings for all chunks
        embeddings = self.embedding_service.embed_texts(chunks)
        
        # 3. Store in Qdrant
        for chunk_index, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
            self.qdrant_client.upsert_vector(
                document_id=document_id,
                chunk_index=chunk_index,
                embedding=embedding,
                payload={
                    "content": chunk_text,
                    "filename": filename,
                    "session_id": session_id
                }
            )
        
        return {
            "document_id": document_id,
            "chunk_count": len(chunks),
            "status": "indexed"
        }
```

### Step 2: Create RAG Chat Service

**File: `services/chat_service_rag.py`**

```python
from services.embedding_service import get_embedding_service
from services.qdrant_client import get_qdrant_client
from services.ollama_client import OllamaClient

class ChatServiceRAG:
    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.qdrant_client = get_qdrant_client()
        self.ollama = OllamaClient()
    
    def retrieve_context(self, query, limit=3, threshold=0.7):
        """Retrieve relevant documents for a query"""
        
        # 1. Embed the query
        query_embedding = self.embedding_service.embed_query(query)
        
        # 2. Search Qdrant
        results = self.qdrant_client.search(
            query_embedding=query_embedding,
            limit=limit,
            score_threshold=threshold
        )
        
        # 3. Return formatted context
        context_items = []
        for result in results:
            context_items.append({
                "content": result["content"],
                "source": result["metadata"].get("filename"),
                "score": result["similarity_score"]
            })
        
        return context_items
    
    def process_message_with_rag(self, session_id, message):
        """Process message with RAG context"""
        
        # 1. Retrieve relevant documents
        context_items = self.retrieve_context(message)
        
        # 2. Build context string
        context = ""
        if context_items:
            context = "Relevant documents:\n"
            for item in context_items:
                context += f"- {item['content']}\n  (Source: {item['source']}, Score: {item['score']:.2f})\n"
        
        # 3. Build augmented prompt
        system_prompt = "You are a helpful assistant..."
        augmented_prompt = f"{context}\n\nQuestion: {message}"
        
        # 4. Generate response
        response = self.ollama.generate(augmented_prompt, system_prompt)
        
        # 5. Return with sources
        return {
            "response": response,
            "sources": context_items,
            "session_id": session_id
        }
```

### Step 3: Update Chat API

**File: `api/chat.py`**

Add RAG-enabled endpoint:

```python
@router.post("/chat/rag", response_model=ChatResponse)
def chat_with_rag(request: ChatRequest, db: Session = Depends(get_db)):
    """Chat with RAG (document-augmented responses)"""
    try:
        service = ChatServiceRAG()
        result = service.process_message_with_rag(request.session_id, request.message)
        
        # Store message in database
        # ...
        
        return {
            "session_id": result["session_id"],
            "response": result["response"],
            "sources": result["sources"]
        }
    except Exception as e:
        logger.error(f"RAG chat failed: {str(e)}")
        raise ChatServiceError(f"RAG processing failed: {str(e)}")
```

---

## Integration with Chat Service

### Option 1: Add RAG as a Flag

```python
class ChatRequest(BaseModel):
    session_id: str
    message: str
    use_rag: bool = True  # Enable RAG by default
    rag_limit: int = 3
    rag_threshold: float = 0.7

@router.post("/chat")
def chat(request: ChatRequest):
    service = ChatServiceRAG()
    
    if request.use_rag:
        result = service.process_message_with_rag(
            request.session_id,
            request.message
        )
    else:
        result = service.process_message(
            request.session_id,
            request.message
        )
    
    return result
```

### Option 2: Always Use RAG

Modify `chat_service_db.py`:

```python
def process_message(self, session_id, message, db):
    """Process with RAG by default"""
    
    # 1. Store user message
    # ...
    
    # 2. Retrieve context from documents
    context_items = self.retrieve_context(message)
    
    # 3. Build augmented prompt
    context_str = self._format_context(context_items)
    augmented_message = f"{context_str}\n\nUser: {message}"
    
    # 4. Generate response
    response = self.ollama.generate(augmented_message)
    
    # 5. Store assistant message
    # ...
    
    return ChatResponse(
        response=response,
        recent_history=recent_messages,
        sources=context_items  # Include sources
    )
```

---

## Example Implementation

### Complete RAG Flow

```python
# 1. User uploads document
POST /documents
{
    "filename": "ai_guide.txt",
    "file_type": "txt",
    "content": "Artificial Intelligence is...",
    "session_id": "uuid"
}

# Response:
{
    "id": "doc-123",
    "chunk_count": 5,
    "status": "indexed"
}

# 2. Backend processes:
# - Chunks document into 5 pieces
# - Generates 5 embeddings
# - Stores in Qdrant

# 3. User asks a question
POST /chat
{
    "session_id": "uuid",
    "message": "What is artificial intelligence?",
    "use_rag": true
}

# 4. Backend:
# - Embeds the question
# - Searches Qdrant
# - Finds similar chunks (score 0.85, 0.82, 0.79)
# - Builds prompt with context
# - Sends to Ollama: "Context: [chunk text]... Question: What is AI?"
# - Gets response from Ollama
# - Returns response + sources

# Response:
{
    "response": "Based on the provided document, AI is...",
    "sources": [
        {
            "content": "Artificial Intelligence is a field of study...",
            "score": 0.85,
            "source": "ai_guide.txt"
        },
        // ... more sources
    ]
}
```

### Python SDK Example

```python
# Initialize services
from services.embedding_service import get_embedding_service
from services.qdrant_client import get_qdrant_client
from services.document_service import DocumentService
from services.chat_service import ChatService

embedder = get_embedding_service()
qdrant = get_qdrant_client()
doc_service = DocumentService()
chat_service = ChatService()

# 1. Upload document
result = doc_service.upload_document(
    filename="knowledge.txt",
    file_type="txt",
    content="Your knowledge base content..."
)
print(f"Document indexed with {result['chunk_count']} chunks")

# 2. Chat with RAG
response = chat_service.process_message_with_rag(
    session_id="user-session",
    message="What do you know about this?"
)
print(f"Response: {response['response']}")
print(f"Sources: {response['sources']}")
```

---

## Testing RAG

### Unit Tests

```python
def test_document_embedding_and_retrieval(self):
    """Test document upload, embedding, and retrieval"""
    
    # Upload document
    doc_result = doc_service.upload_document(
        filename="test.txt",
        file_type="txt",
        content="Test document with information"
    )
    
    # Search for similar content
    query = "information about test"
    results = qdrant.search(
        query_embedding=embedder.embed_query(query),
        limit=5
    )
    
    # Verify results
    assert len(results) > 0
    assert results[0]["similarity_score"] > 0.5
```

### Integration Test

```python
def test_rag_chat_flow(self):
    """Test complete RAG chat flow"""
    
    # 1. Upload document
    doc = doc_service.upload_document(
        filename="faq.txt",
        file_type="txt",
        content="Q: How to use RAG?\nA: Upload documents and ask questions..."
    )
    
    # 2. Chat with RAG
    response = chat_service.process_message_with_rag(
        session_id="test-session",
        message="How do I use RAG?"
    )
    
    # 3. Verify
    assert "response" in response
    assert "sources" in response
    assert len(response["sources"]) > 0
    assert response["sources"][0]["similarity_score"] > 0.7
```

### Manual Testing

```bash
# 1. Start services
docker run -p 6333:6333 qdrant/qdrant  # Qdrant
ollama serve  # Ollama
python -m uvicorn main:app --reload  # Backend

# 2. Upload document
curl -X POST http://localhost:8000/documents \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "test.txt",
    "file_type": "txt",
    "content": "RAG allows AI to answer questions based on documents"
  }'

# 3. Chat with RAG
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-123",
    "message": "What does RAG allow?",
    "use_rag": true
  }'

# 4. Check response includes sources
```

---

## Performance Considerations

### Optimize for Speed

```python
# 1. Cache embeddings
embedding_cache = {}

def get_or_embed_query(query):
    if query not in embedding_cache:
        embedding_cache[query] = embedder.embed_query(query)
    return embedding_cache[query]

# 2. Use smaller embedding model
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Fast and lightweight

# 3. Limit search scope
results = qdrant.search(
    query_embedding=embedding,
    limit=3,  # Only top 3
    score_threshold=0.75  # Filter low scores
)

# 4. Batch operations
# Embed multiple chunks at once instead of one-by-one
embeddings = embedder.embed_texts(chunks)  # Faster
```

### Optimize for Quality

```python
# 1. Use larger embedding model
EMBEDDING_MODEL = "all-mpnet-base-v2"  # Better quality

# 2. Increase context window
results = qdrant.search(limit=5)  # More context

# 3. Lower threshold for more results
results = qdrant.search(score_threshold=0.5)

# 4. Better chunking
chunks = doc_service.chunk_text(
    content,
    chunk_size=1500,  # Larger chunks
    chunk_overlap=200
)
```

---

## Next Steps

1. ✅ Set up Qdrant server
2. ✅ Install embedding model
3. Implement `DocumentService.upload_document_with_embeddings()`
4. Implement `ChatServiceRAG`
5. Update chat API with RAG endpoint
6. Test with sample documents
7. Integrate with frontend
8. Add search UI for document retrieval

---

## Troubleshooting

### Query returns no results

```python
# 1. Check embeddings are stored
info = qdrant.get_collection_info()
print(f"Total vectors: {info['points_count']}")

# 2. Lower threshold
results = qdrant.search(
    query_embedding=embedding,
    score_threshold=0.0  # Accept all results
)

# 3. Check documents were indexed
# Use test_qdrant.py to verify setup
```

### Slow responses

```python
# 1. Use GPU for embeddings
EMBEDDING_DEVICE = "cuda"

# 2. Reduce search limit
limit = 3  # Instead of 10

# 3. Use faster model
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
```

### Irrelevant results

```python
# 1. Improve chunking
chunk_size = 800  # Smaller chunks
chunk_overlap = 100

# 2. Increase threshold
score_threshold = 0.75  # Only very similar

# 3. Add metadata filtering
results = qdrant.search(
    query_embedding=embedding,
    filters={"filename": "specific_doc.txt"}
)
```

---

## Resources

- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [RAG Introduction](https://www.example.com)
- [SentenceTransformers](https://www.sbert.net/)
- [Vector Search Best Practices](https://www.example.com)
