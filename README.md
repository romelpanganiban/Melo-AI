# Melo-AI

Memory-Enhanced Engine for Local Operations

Melo-AI is a local-first AI assistant designed to provide
conversation memory, document intelligence, coding assistance,
and personal productivity tools while running on your own hardware.

---

## Vision

Melo-AI is a local-first AI assistant inspired by Claude, ChatGPT, and Open WebUI.

The goal is to build an AI assistant that can:

- Chat naturally
- Remember conversations
- Manage multiple chat sessions
- Analyze documents
- Search knowledge bases
- Assist with coding
- Run completely locally
- Support voice interactions
- Fine-tune with Unsloth

---

## Current Status

Early development. The current implementation includes database-backed chat,
document ingestion, RAG, private knowledge collections, grounded intelligence
modes, coding tools, and bounded read-only agent actions.

### Completed

#### Backend Core

- FastAPI Backend
- Health Endpoint
- Chat Endpoint
- Streaming Chat Endpoint (`/chat/stream`)
- Service health reporting for Ollama and Qdrant
- Swagger Documentation

#### Memory System

- JSON Memory System
- Persistent Chat History
- Conversation Memory

#### Session System

- Create Sessions
- Read Sessions
- Rename Sessions
- Delete Sessions

#### Chat Experience

- Real-time token streaming from Ollama
- Live typing effect in frontend while model responds
- No manual refresh needed after sending a message
- Session-based history loaded from database
- Automatic session titles from the first user message

#### Document Intelligence (RAG)

- Document Upload System
- TXT, PDF, and DOCX file uploads
- PDF/DOCX text extraction with `pypdf` and `python-docx`
- Automatic Text Chunking (1000 words, 150 word overlap)
- Vector Embeddings (all-MiniLM-L6-v2, 384 dimensions)
- Qdrant Vector Database Integration
- Semantic Similarity Search
- Document Context in Chat
- Source Attribution
- Source display in assistant messages
- Batch Embedding Generation

#### Intelligence Modes

- Ask mode with grounded filename citations
- Study mode with summaries, flashcards, quizzes, and explanations
- Plan mode with grounded ordered plans
- Auto mode with task-aware mode selection
- Agent proposals and bounded read-only actions
- Persistent learning preferences and study progress

#### Vector Database

- Qdrant Vector DB (Local + Cloud Support)
- Collection Management
- Vector Storage & Retrieval
- Metadata Payload Storage
- Health Monitoring

#### Settings System

- Settings API
- Settings Manager
- Configuration Management

#### Architecture

- Service Layer
- Configuration Layer
- Modular Project Structure
- Database-backed sessions and messages

#### Database Migrations

PostgreSQL schema changes are tracked with Alembic. From the `backend`
directory, apply them with:

```bash
alembic upgrade head
```

The local `backend/.env` supplies `DATABASE_URL` and is ignored by Git.

#### Testing

- Pytest Setup
- Unit Tests
- API Tests

### Current Validation

- Backend: 192 tests passing
- Frontend: 34 tests passing, lint passing, production build passing
- Known warnings: deprecated Starlette status constants, deprecated TestClient/httpx compatibility, and optional CUDA/Qdrant availability warnings

See [SYSTEM_AUDIT.md](SYSTEM_AUDIT.md) for the system-wide findings and prioritized improvements.

---

## Latest Update

**Knowledge Base and RAG - Implemented**

- Implemented document-enhanced chat using Qdrant vector database
- Documents automatically chunked and embedded when uploaded
- Chat searches documents for relevant context
- AI responses now augmented with document knowledge
- Chat responses include document sources and relevance scores
- Fixed logging system to properly handle extra fields
- Improved DocumentsPanel UX with better labels, help text, and feedback
- SentenceTransformers embeddings (384-dimensional vectors)
- Batch embedding generation for efficiency
- Offline-capable (models pre-cached locally)
- Multipart file uploads with a 10 MB limit
- Health endpoint reports optional service availability

**Files Changed:**
- `services/document_service.py` - Added embedding generation on upload
- `services/chat_service.py` - Added document search and context injection
- `api/chat.py` - Added sources to chat response
- `components/DocumentsPanel.tsx` - Complete UX overhaul
- `core/logging.py` - Fixed LogRecord handling

---

## Previous Update (v0.1.2)

- Added backend streaming endpoint using NDJSON event chunks.
- Added streaming support in Ollama client and chat service.
- Updated frontend chat flow to render messages in real time without refresh polling.
- Added live streaming cursor in assistant message bubble.
- Improved chat response latency perception with incremental rendering.

---

## Hardware Target

- Ryzen 7 7700
- RX 9060 XT 16GB
- 32GB RAM
- 1TB SSD

---

## Future Integrations

### Local AI

- Ollama
- Qwen3-8B
- Qwen2.5-Coder

### Knowledge Base

- PDF Processing (implemented)
- DOCX Processing (implemented)
- TXT Processing (implemented)
- Qdrant
- Retrieval-Augmented Generation (RAG)

### Training

- Unsloth
- Qwen Fine-Tuning

### Voice

- Whisper
- Kokoro TTS

---

## Platform Direction

Melo-AI is intended to become a model-agnostic AI platform. Melo owns the
knowledge, context, memory, permissions, tools, approvals, workflows, and user
experience; Ollama and future hosted models are replaceable providers.

The next major investment is authentication and authorization before exposing
the system beyond localhost. This is followed by retrieval quality, reliable
multi-step agents, durable user/workspace/task memory, provider routing, and
evaluation.

### Usage Limits

Normal users have a configurable monthly token budget. Set
`MONTHLY_TOKEN_LIMIT` in `backend/.env`; the default is `100000` tokens.
Usage is available from `GET /usage`. The configured `ADMIN_EMAIL` is exempt
from the monthly token budget.

## Future Vision

After the local-first version is completed, Melo-AI may expand to support:

- Cloud Deployment
- User Accounts
- Multi-Device Sync
- Team Workspaces
- Subscription Plans
- Hosted AI Models
- SaaS Platform

---

## Goal

Create a personal, local-first AI assistant that combines:

- Claude-style conversations
- ChatGPT-style usability
- Open WebUI flexibility
- Local AI privacy

while remaining fully owned and controlled by the user.