# Melo-AI Architecture

Current Architecture

User
 ↓
FastAPI
 ↓
Chat API
 ↓
Memory Manager
 ↓
chat_history.json

Session API
 ↓
Session Manager
 ↓
sessions.json

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