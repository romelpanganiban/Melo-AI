# Melo-AI Architecture

## Current Architecture

User
 ↓
Frontend (Next.js)
 ↓
FastAPI Backend
 ↓
Chat API (`/chat`, `/chat/stream`)
 ↓
Chat Service
 ↓
Ollama Client
 ↓
Ollama Server
 ↓
Streamed Tokens / Final Response

Session and document APIs (`/sessions`, `/documents`)
 ↓
Session/Document Services
 ↓
Database Repositories
 ↓
SQLite or PostgreSQL (`sessions`, `messages`, `settings`, `documents`, `document_chunks`)

Document ingestion:

`POST /documents/upload`
 ↓
TXT/PDF/DOCX text extraction
 ↓
Document Service
 ↓
Chunk storage + optional embeddings
 ↓
Qdrant vector collection

---

Chat Streaming Flow

User Message
 ↓
`POST /chat/stream`
 ↓
Store user message in DB
 ↓
Request Ollama with stream=true
 ↓
Search session documents through embeddings and Qdrant
 ↓
Inject retrieved context into the Ollama prompt
 ↓
Backend emits NDJSON chunks (`chunk`)
 ↓
Frontend appends chunk text live
 ↓
Backend stores final assistant message
 ↓
Backend emits `done` with document sources

## Planned Components

- Ollama
- Qwen3-8B
- Qwen2.5-Coder
- Qdrant
- Unsloth
- Whisper
- PostgreSQL