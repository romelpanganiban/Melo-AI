# Melo-AI Roadmap

## Phase 1 - Foundation ✅

- [x] Create Repository
- [x] Setup GitHub
- [x] Create Project Structure
- [x] Setup Python Environment
- [x] FastAPI Installation
- [x] Uvicorn Setup

---

## Phase 2 - Backend ✅

- [x] Health Endpoint
- [x] Chat Endpoint
- [x] Swagger Documentation
- [x] JSON Storage

---

## Phase 3 - Memory ✅

- [x] Memory Manager
- [x] Persistent Chat History
- [x] Message Storage
- [x] History Retrieval

---

## Phase 4 - Sessions ✅

- [x] Session Manager
- [x] Create Sessions
- [x] Read Sessions
- [x] Delete Sessions
- [x] Rename Sessions

---

## Phase 5 - Backend Architecture ✅

- [x] Service Layer
- [x] Settings Manager
- [x] Settings API
- [x] Configuration Management
- [x] Logging
- [x] Unit Testing
- [x] API Testing

---

## Milestone 5.1 - Backend Hardening ✅

Status: Completed

- [x] Session-Based Memory
- [x] Chat API Tests
- [x] Service Tests
- [x] Custom Exceptions
- [x] Logging
- [x] Agent Structure

Deliverable:
ChatGPT/Claude-style Session Memory and Hardened Backend

---

## Phase 6 - Frontend ✅

- [x] Next.js
- [x] Chat UI
- [x] Sidebar
- [x] Session List
- [x] Session Selection
- [x] Send Message
- [x] Message History
- [x] Settings Page

---

## Phase 7 - Local AI

- [x] Local AI integration
- [x] Install Ollama
- [x] Install Qwen3-8B
- [x] Connect Ollama API
- [x] Replace Mock Responses

---

## Phase 8 - Knowledge Base ✅

- [x] PDF parsing and upload
- [x] DOCX parsing and upload
- [x] Text chunking for pasted content
- [x] Vector search for indexed content
- [x] TXT, PDF, and DOCX file picker
- [x] Document chunk viewer

---

## Phase 9 - RAG ✅

- [x] Qdrant integration
- [x] Embeddings
- [x] Retrieval pipeline
- [x] Context injection into chat
- [x] Source metadata in API responses
- [x] Source display in assistant messages
- [x] Graceful fallback when Qdrant or embeddings are unavailable

---

## Phase 10 - Coding Assistant ✅

- [x] Frontend workspace for read-only file inspection and code analysis
- [x] AI code review and generation proposals
- [x] Read-only code analysis API
- [x] Python structure analysis
- [x] JavaScript/TypeScript structure analysis
- [x] Workspace path and file-size safety limits
- [x] Read-only workspace file endpoint
- [x] Confirmation-gated file writes
- [x] Atomic workspace file replacement
- [x] Confirmation-gated file deletion
- [x] Git Integration
- [x] Git branch, status, diff, staging, and confirmation-gated commits

---

## Phase 11 - Private Knowledge & Intelligence Modes

- [x] Request-scoped Ask mode with grounded answers and filename citations
- [x] Standalone session-scoped semantic document search
- [x] Study mode with summaries, flashcards, quizzes, and explanations
- [x] Plan mode with grounded ordered action plans
- [x] Auto mode with task-aware response mode selection
- [x] Private knowledge workspace and document collections
- [x] Agent mode proposal flow with tool intent and approval points
- [x] Agent mode bounded read-only tool execution
- [x] Approval token primitive for side-effecting Agent actions
- [ ] Agent mode with multi-step tool execution
- [ ] Approval gates for file, Git, and other side-effecting actions
- [ ] Auto mode with task-aware model selection
- [x] Persistent learning preferences and study progress

Deliverable:
Local knowledge assistant with Ask, Study, Plan, Agent, and Auto modes

Implementation boundary:
- Completed locally: grounded modes, collections, study persistence, citations,
	agent proposals, bounded read-only actions, and approval-token primitives.
- Not yet production-safe: workspace roles, full tenant isolation, and
	side-effecting agent execution.

## Platform Direction

### Security Review Checkpoint - 2026-08-27

- [x] Complete a read-only system and security review
- [x] Record localhost and hosted-deployment security ratings
- [x] Identify authorization, filesystem isolation, upload, token, rate-limit,
      and deployment hardening gaps
- [ ] Resolve high-priority authorization and isolation findings before shared
      or internet-facing deployment

The current review rates Melo-AI **6/10 overall**, **5/10 for single-user
localhost use**, and **3/10 for shared or internet-facing deployment**. See
`SYSTEM_AUDIT.md` for the evidence, validation status, and remediation order.

Melo-AI should be developed as a model-agnostic AI platform rather than a thin
chat wrapper. Melo's durable value is the orchestration around the model:

- Knowledge engine: classification, structure-aware chunking, retrieval,
	reranking, context compression, and citations.
- Context and memory engine: conversation, user, workspace, and task context
	with explicit retention and permission rules.
- Agent and tool engine: planning, bounded execution, approvals, observation,
	verification, and audit history.
- Permission engine: authenticated users, workspace ownership, roles, and
	document/tool access checks before retrieval or execution.
- Model provider layer: one interface for Ollama and future hosted providers,
	with task-aware routing and usage/cost tracking.
- Workflow engine: repeatable scheduled or event-triggered document and tool
	workflows.

Recommended delivery order:
1. Workspace roles, resource migration to workspace scope, and production authorization policy.
2. Retrieval quality and citation correctness.
3. Reliable multi-step agents with sandboxing and approvals.
4. Durable memory and context policies.
5. Provider abstraction, model routing, evaluation, and workflows.

The local machine is sufficient for developing and validating this architecture.
Production inference and multi-user capacity should move to appropriately sized
hosted infrastructure when the product is deployed.

---

## Phase 12 - Fine Tuning

- [x] Dataset Preparation (JSONL conversation datasets and UI)
- [x] Unsloth Setup
- [ ] Qwen3 Fine-Tuning

---

## Phase 13 - Cloud Platform

- [x] User Accounts
- [x] Authentication
- [ ] Database
- [ ] Deployment
- [ ] Usage Tracking

Deliverable:
Hosted Melo-AI Platform

---

## Phase 14 - Subscriptions

- [ ] Free Tier
- [ ] Pro Tier
- [ ] Payment Integration
- [ ] Subscription Management
- [ ] Billing Dashboard

Deliverable:
Commercial SaaS Version

## Version 1.0

- [x] Local Claude Alternative
- [x] Memory
- [x] Sessions
- [x] RAG
- [x] Coding Assistant
- [x] Ask, Study, Plan, and Auto modes
- [x] Agent proposal and bounded read-only actions

---

## Version 1.1 - Cloud Readiness

- [x] Backend authentication and user accounts
- [x] Frontend login and token handling
- [x] Default workspace creation and membership roles
- [ ] Organizations and workspace ownership across multiple workspaces
- [x] Workspace-scoped sessions, documents, collections, and vector retrieval
- [x] Workspace-scoped study progress and Agent document search
- [ ] Workspace-scoped settings, training, approvals, and coding tool policies
- [x] PostgreSQL database initialization and configuration support
- [ ] PostgreSQL as the single production source of truth
- [x] Alembic database migrations
- [ ] Rate limits, quotas, and token usage ledger
- [x] Monthly token usage ledger and credit-limit enforcement
- [x] Configured admin-exempt request rate limits
- [ ] Distributed rate limits, quotas, and token usage ledger
- [ ] Secure production configuration and secret management
- [ ] Sandbox or disable server file and Git tools
- [x] Disable shared file/Git tools by default until workspace roots exist
- [ ] Provider abstraction for hosted Qwen and other model APIs
- [ ] Production deployment, backups, monitoring, and CI/CD

Deliverable:
Secure multi-tenant cloud foundation for Melo-AI
