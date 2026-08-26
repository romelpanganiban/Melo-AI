# Features

## Implemented

### Chat
- Multi-chat
- Conversation history
- Streaming responses
- Markdown code blocks with copy support

### Coding
- Workspace file inspection
- Code structure analysis
- Code generation
- AI code review
- Confirmation-gated file save and deletion
- Git status, diff, staging, and confirmation-gated commits

### Memory
- Session-scoped conversation memory
- Persistent learning preferences and study progress

### Authentication
- User registration and login
- Signed bearer-token authentication
- Logout and current-token revocation
- Authenticated API access for private resources and tools

### Intelligence Modes
- Ask mode with grounded filename citations
- Study mode with summaries, flashcards, quizzes, and explanations
- Plan mode with grounded ordered plans
- Auto mode with task-aware mode selection
- Agent mode proposal flow
- Bounded read-only Agent actions for file reads, code analysis, and document search

### Training
- Conversation dataset preparation
- JSONL export for fine-tuning
- Unsloth environment setup

### Documents
- PDF analysis
- DOCX analysis
- TXT, PDF, and DOCX upload
- RAG retrieval and source attribution
- Named knowledge collections
- Collection-aware chat retrieval
- Deduplicated source metadata with document and chunk identifiers

### UI
- Light and Dark appearance modes

## Planned

### Platform
- Default workspace and membership creation
- Authenticated workspace listing
- Organizations, workspaces, roles, and tenant isolation
- Frontend workspace authorization policies
- Provider abstraction and task-aware model routing
- Durable user, workspace, and task memory
- Retrieval evaluation, answer grounding checks, latency, usage, and cost metrics

### Knowledge Engine
- Hybrid keyword and semantic retrieval
- Reranking and context compression
- Page/section-level citation mapping
- Advanced permission-aware retrieval for workspace roles

### Agents and Workflows
- Multi-step tool execution with replanning and verification
- Approval gates for all side-effecting actions
- Sandboxed file and Git operations
- Scheduled and event-triggered workflows

### Training
- Qwen3 fine-tuning

### Productivity
- Tasks, reminders, and calendar tools

### Voice
- Whisper speech-to-text
- Kokoro text-to-speech