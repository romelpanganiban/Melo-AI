# Melo-AI Architecture

## Product Direction

Melo-AI is a local-first, model-agnostic AI platform. The model is one replaceable
component; Melo owns the context, knowledge, memory, tools, approvals, and user
experience around it.

The current implementation is a strong local foundation for that direction. It
already provides persistent sessions, document ingestion and retrieval, grounded
response modes, code analysis, Git operations, bounded read-only agent actions,
and authenticated default workspaces. Resource migration to workspace scope,
advanced retrieval, and production-grade agent execution remain future work.

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

## Current Intelligence Flow

For a mode-aware request, the backend currently follows this shape:

User request
 ↓
Chat mode selection (`chat`, `ask`, `study`, `plan`, `agent`, or `auto`)
 ↓
Session and collection-scoped context
 ↓
Semantic document retrieval through embeddings and Qdrant
 ↓
Grounded prompt construction with source metadata where supported
 ↓
Ollama model generation
 ↓
Persisted response and source/mode metadata

Ask, Study, and Plan modes specialize the prompt and response contract. Agent
mode currently supports bounded read-only actions such as file reads, code
analysis, and document search. Side-effecting actions require workspace policy
and sandboxing; approval tokens are bound to the authenticated user but do not
replace authorization.

---

Chat Streaming Flow

User Message
 ↓
`POST /chat/stream`
 ↓
Store user message in DB
Search session documents through embeddings and Qdrant
 ↓
Inject retrieved context into the Ollama prompt
 ↓
Request Ollama with stream=true
 ↓
Backend emits NDJSON chunks (`chunk`)
 ↓
Frontend appends chunk text live
 ↓
Backend stores final assistant message
 ↓
Backend emits `done` with document sources

## Target Platform Architecture

The longer-term platform can grow along these boundaries without coupling the
application to a specific model vendor:

Melo request
 ↓
Authentication and workspace authorization
 ↓
Intent and mode routing
 ↓
Context engine
 ├── Conversation/session memory
 ├── User, workspace, and task memory
 ├── Permission-filtered knowledge retrieval
 └── Tool and approval context
 ↓
Knowledge, agent, or workflow execution
 ↓
Model provider interface and model router
 ├── Ollama/local models
 ├── Hosted Qwen or other providers
 └── Premium providers when configured
 ↓
Grounded, observable response with citations and usage data

This is a target architecture, not a claim that every box is implemented today.

## Learning and Personalization Architecture

Melo should evolve as a retrieval-first assistant with a separate learning layer, rather than turning every chat interaction into uncontrolled model updates.

### Architecture Layers

User interaction
 ↓
Authentication + workspace authorization
 ↓
Context engine
 ├── Session memory
 ├── Workspace memory
 ├── Personal preferences
 ├── Document RAG retrieval
 └── Approved feedback ledger
 ↓
Learning control plane
 ├── Feedback capture and moderation
 ├── Preference and style memory
 ├── Training dataset builder
 ├── Safety validation and quality checks
 └── Periodic PEFT/LoRA adapter updates
 ↓
Model provider interface
 ├── Local Ollama models
 ├── Hosted model adapters
 └── Versioned model registry
 ↓
Grounded response with citations, memory, and safe personalization

### Design principles

- Retrieval is the default knowledge source.
- Personalization is opt-in and workspace-scoped.
- Raw chat traffic is never directly promoted to training without review.
- Approved examples go through a dataset pipeline and model evaluation before deployment.
- Training updates are versioned, reversible, and auditable.
- Model behavior changes are isolated behind adapters or controlled model versions.

### Safe learning loop

1. User feedback is captured as explicit signals: thumbs up/down, corrections, saved preferences, or accepted suggestions.
2. The backend writes those signals to a structured learning ledger with timestamps, user, and workspace metadata.
3. Approved examples are filtered, deduplicated, and trimmed for privacy safety.
4. A curated dataset builder exports training examples for a validation and fine-tuning workflow.
5. A PEFT/LoRA-style adapter is trained and benchmarked against a regression set.
6. The new adapter is deployed behind version control and can be rolled back without affecting the base model.

### Governance and safety

- Training data must be consented, reviewed, and scoped by workspace and user.
- Sensitive or unreviewed content must not be used for unsupervised training.
- Personal memory and training memory must stay separate.
- Every training decision should produce an audit record for traceability and rollback.

## Planned Components

- Ollama
- Qwen3-8B
- Qwen2.5-Coder
- Qdrant
- Unsloth
- Whisper
- PostgreSQL

## Priority Order

1. Workspace roles, authorization policy, and full multi-workspace tenant isolation.
2. Retrieval quality: hybrid search, reranking, context compression, and robust
	citation mapping.
3. Reliable agent execution: multi-step plans, approval gates, sandboxing, and
	verification after tool actions.
4. Durable memory and context policies for users, workspaces, and tasks.
5. Provider abstraction, model routing, evaluation, usage tracking, and workflows.