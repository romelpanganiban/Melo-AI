# Changelog

## Unreleased

### Added

#### Knowledge Base and RAG

- TXT, PDF, and DOCX document uploads through `POST /documents/upload`
- PDF text extraction with `pypdf`
- DOCX text extraction with `python-docx`
- Document chunking, embeddings, Qdrant indexing, and retrieval
- Document source metadata in chat responses and assistant messages
- Qdrant vector cleanup when documents are deleted

#### Coding Assistant

- Read-only code analysis through `POST /analysis/code`
- Workspace file reading through `POST /files/read`
- Confirmation-gated file writes through `POST /files/write`
- Confirmation-gated file deletion through `DELETE /files`
- Python AST analysis and JavaScript/TypeScript structure detection
- Workspace path, protected-directory, file-type, and file-size safeguards
- Atomic file replacement for safe updates

### Improved

- Automatic session titles generated from the first user message
- Sidebar refresh after a chat response so generated titles appear immediately
- Health endpoint reporting for Ollama, the configured model, and Qdrant
- Document panel overflow handling and chunk viewing layout
- Frontend test configuration and stale component test contracts

## v0.1.2

### Added

#### Real-time Chat

- Streaming chat API endpoint: `POST /chat/stream`
- NDJSON chunk events (`chunk`, `done`, `error`) for progressive responses
- Ollama streaming client support in backend service layer

#### Frontend Chat UX

- Real-time assistant token rendering in chat window
- Live typing cursor while response is streaming
- Removed refresh-based message update flow after send

### Improved

- Reduced repeated Ollama availability checks per request
- Fixed database session close behavior in chat service when using injected DB session

---

## v0.1.1

### Added

#### Backend Architecture

- Service Layer
- Configuration System
- Logger Setup
- Custom Exceptions

#### Session System

- Session Creation
- Session Retrieval
- Session Rename
- Session Delete
- Session-Based Memory

#### Settings System

- Settings Manager
- Settings API

#### Testing

- Pytest Setup
- Memory Manager Tests
- Session Manager Tests
- Settings Manager Tests
- Chat API Tests
- Settings API Tests
- Session API Tests

#### Project Structure

- Agents Directory
- Models Directory
- RAG Directory
- Tools Directory

---

## v0.1.0

### Added

#### Backend Core

- FastAPI Backend
- Swagger UI
- Health Endpoint
- Chat Endpoint

#### Memory System

- Memory Manager
- History Endpoint
- JSON Persistence