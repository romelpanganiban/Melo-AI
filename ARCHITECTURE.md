# Melo-AI Architecture

Current Architecture

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

Session API (`/sessions`)
 ↓
Session Service
 ↓
Database Repositories
 ↓
SQLite (`sessions`, `messages`, `settings`, `documents`)

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
Backend emits NDJSON chunks (`chunk`)
 ↓
Frontend appends chunk text live
 ↓
Backend stores final assistant message
 ↓
Backend emits `done`

---

Future Architecture

User
 ↓
Frontend (Next.js)
 ↓
Backend (FastAPI)
 ↓
Session Manager
 ↓
Memory Manager
 ↓
RAG Engine
 ↓
Ollama
 ↓
Qwen3-8B
 ↓
Response

---

Future Components

- Ollama
- Qwen3-8B
- Qwen2.5-Coder
- Qdrant
- Unsloth
- Whisper
- PostgreSQL