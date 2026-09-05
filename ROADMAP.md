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

## Recommended Development Sequence

The following order reflects the highest-risk issues first and keeps the roadmap
secure, stable, and production-ready before scaling:

### Sprint 1 - Security

1. Fix chunk authorization
2. Make security context mandatory
3. Audit all endpoints
4. Add two-user tests

### Sprint 2 - Identity

5. Fix admin bootstrap
6. Harden sessions
7. Durable token revocation

### Sprint 3 - AI Security

8. Prompt injection handling
9. Sensitive-file policy
10. Agent authorization

### Sprint 4 - Reliability

11. Upload limits
12. Processing queue
13. Document states
14. Qdrant retry/reconciliation

### Sprint 5 - Scale

15. Redis
16. Per-operation rate limits
17. Worker architecture
18. Resource quotas

### Sprint 6 - Production

19. HTTPS
20. Security headers
21. Reverse proxy
22. Trusted proxy configuration

### Sprint 7 - Security Automation

23. Security tests
24. pip-audit
25. npm audit
26. Bandit/Semgrep
27. CodeQL

### Sprint 8 - Documentation

28. Update SYSTEM_AUDIT.md
29. Update SECURITY_ARCHITECTURE.md
30. Document SaaS deployment requirements

This sequence is the recommended delivery plan before shared or internet-facing
production rollout.

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

## Phase 14 - Production Security Hardening

Status: In Progress (Phase 14a Complete)

### Phase 14a - Central Authorization Middleware ✅ (Commit: f2ec20b)

Completed:
- [x] AuthorizationPolicy engine (core/authz.py) with centralized decision logic
- [x] WorkspaceContext and require_workspace_access middleware (core/auth.py)
- [x] Comprehensive test suite (28 tests) for policy validation
- [x] Workspace membership enforcement (read/write/admin)
- [x] Document ownership and sharing policy
- [x] Tool capability role-gating (owner/editor/viewer/guest)
- [x] Approval token binding validation
- [x] Database-backed authorization checks

Deliverables:
- backend/core/authz.py (~550 lines): Centralized authorization policy
- backend/core/auth.py (enhanced): Middleware for workspace-scoped requests
- backend/tests/test_authz_policy.py (~650 lines): Full test coverage
- Documentation: SECURITY_ARCHITECTURE_IMPLEMENTATION.md (6-phase hardening roadmap)

Next: Retrofit existing endpoints (api/chat.py, api/sessions.py, api/documents.py, etc.) to use require_workspace_access middleware.

### Critical / must implement next

- [x] Central authorization middleware for all authenticated endpoints and tool actions
- [x] Workspace membership enforcement on every read/write/delete/query by workspace
- [x] Document ownership enforcement for document retrieval, updates, and deletion
- [x] Qdrant tenant isolation with workspace-scoped filters and private vector indexes
- [x] Path traversal protection for file access, uploads, and workspace operations
- [x] Workspace filesystem sandbox with per-workspace root isolation and deny-by-default access
- [x] Agent capability allowlist restricting available tools, resources, and side effects (Phase 14d)
- [x] Action-bound approvals for all mutating agent operations and Git/file changes (Phase 14d)
- [ ] Secret isolation so agents and tool execution never receive raw credentials or production secrets (Phase 14e)
- [x] Git safety policy with repo-bound operations, branch restrictions, and diff review checks

### High priority hardening

- [x] Upload/resource limits for file size, parsing expansion, embedding workload, and concurrency
- [x] Redis-backed distributed rate limiting and atomic quota enforcement for multi-instance deployment
- [x] Secure session/token handling, including XSS-resistant storage, rotation, expiration, and durable revocation
- [ ] Security audit logs for auth, workspace actions, approvals, file mutations, and admin operations
- [x] Security regression tests covering cross-user access, secret leakage, approval bypass, and tenant isolation
- [ ] Dependency and SAST scanning in CI for vulnerable packages and dangerous patterns
- [x] Prompt-injection and RAG security tests for retrieval poisoning, prompt leakage, and unsafe context handling
- [ ] Production security configuration for TLS, reverse proxy headers, CORS allowlists, and deployment defaults

### Delivery expectation

This phase should close the remaining gaps that currently reduce Melo-AI to a strong localhost prototype rather than a production-safe multi-user platform. It is required before enabling shared deployments, public networking, or multi-tenant workspace use.

---

## Milestone 14.2 - Melo Security Hardening v2

Status: Planned

The next milestone is security hardening rather than another AI feature. Work should be completed in this order:

1. [x] Replace `ADMIN_EMAIL` privilege with database roles
2. [x] Define private/shared workspace document policy
3. [x] Centralize authorization
4. [x] Apply identical authorization policy to PostgreSQL + Qdrant
5. [x] Create real per-workspace filesystem roots
6. [x] Sandbox workspace/Git operations
7. [x] Durable session/revocation
8. [x] Redis-based distributed rate limits
9. [x] Document processing resource limits
10. [x] Qdrant/SQL reconciliation hardening (chunk-level audit, failure-safe repair, and focused test completion)
11. [x] Prompt-injection defense for RAG/agents
12. [x] Cross-tenant security regression tests
13. [x] Fix README's stale test results
14. [x] Remove committed `__pycache__`
15. [x] Run a clean backend test environment

**Status: Milestone 14.2 In Progress** - Agent capability and approval controls are complete; secret isolation, audit logging, and production security configuration remain.

---

## Phase 15 - Safe Online Learning & Personalization

Status: Planned after the security hardening milestones are complete

### Goal

Add adaptive learning without turning the system into unsafe or unstable online model training. Melo should improve through safe memory, feedback capture, curated examples, and periodic training workflows rather than by directly mutating the base model during every chat.

### Phase 15.1 - Learning Data Pipeline

- [ ] Capture user feedback signals: thumbs up/down, corrections, explicit preferences, and save-to-memory actions
- [ ] Store feedback in a structured learning ledger with user, workspace, timestamp, source, and rationale
- [ ] Separate raw memory from approved training examples to avoid poisoning the model with low-quality chat content
- [ ] Add review and moderation workflow for examples before they become training data
- [ ] Define safe retention and deletion policies for learning data and preference memory

### Phase 15.2 - Personal Memory Layer

- [ ] Persist user preferences, writing style, domain context, and learning goals by workspace or user
- [ ] Add retrieval of personal memory alongside document RAG for context personalization
- [ ] Support opt-in personalization toggles and explicit override controls
- [ ] Keep personal memory isolated by workspace and user, with audit logging for access and changes

### Phase 15.3 - Curated Training Data Engine

- [ ] Convert approved interactions into JSONL examples for fine-tuning or PEFT workflows
- [ ] Tag examples by task type: chat, ask, plan, study, coding, summarization, RAG grounding
- [ ] Validate data quality, duplicate suppression, and prompt safety before training exports
- [ ] Add dataset versioning and human review for every training snapshot

### Phase 15.4 - Safe Fine-Tuning / Adapter Training

- [ ] Use LoRA or PEFT-based adapters instead of direct full-model retraining for local-first tuning
- [ ] Train only on approved, de-duplicated, privacy-safe examples
- [ ] Benchmark before and after with evaluation prompts and regression checks
- [ ] Keep a rollback path to previous adapters and model weights
- [ ] Expose adapter selection per workspace or user profile when needed

### Phase 15.5 - Feedback-Driven Improvement Loop

- [ ] Measure response quality with rating signals, acceptance rates, and citation usefulness
- [ ] Run periodic quality evaluation jobs over a holdout set of prompts
- [ ] Promote only high-confidence examples into the training queue
- [ ] Prevent low-quality or adversarial prompts from silently poisoning the model

### Phase 15.6 - Governance and Safety Controls

- [ ] Block training on sensitive or unreviewed user content by default
- [ ] Require admin approval for large-scale training dataset ingestion
- [ ] Add opt-in consent for personalization and learning pipelines
- [ ] Log every training/export/review decision with traceability
- [ ] Keep a clear separation between retrieval memory and training memory

### Implementation sequence

1. Safe feedback capture and learning ledger
2. Personal memory and preference isolation
3. Approved dataset generation and validation
4. Fine-tuning adapters with rollback and evaluation
5. Periodic improvement loop and governance reviews

### Decision rule

Melo should improve through curated learning, verified memory, and periodic safe training workflows. It should not directly self-train from raw chat traffic or unreviewed agent actions.

---

## Phase 16 - Subscriptions

- [ ] Free Tier
- [ ] Pro Tier
- [ ] Payment Integration - final technical task after the product and platform are ready
- [ ] Subscription Management
- [ ] Billing Dashboard

Payment integration is intentionally the final Phase 14 implementation task.
Business permits, tax registration, legal agreements, identity verification,
merchant onboarding, and other compliance documents are postponed until the
business requirements and documentation are available. The software work can
be prepared beforehand, but live payment activation must wait for those
business approvals.

Deliverable:
Commercial SaaS Version (payment activation pending business and compliance readiness)

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
