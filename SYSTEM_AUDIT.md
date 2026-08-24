# System Audit

Date: 2026-08-24

## Verified Changes

- Dataset creation now supports output directories outside the repository, including temporary and external deployment directories.
- `ENABLE_CORS=false` now disables CORS middleware as configured.
- `MessageInput` remains compatible when model selector props are omitted.
- Frontend tests now match the current message bubble and chat empty/loading states.

## Validation

- Backend: `157 passed`
- Frontend: `29 passed`
- Frontend lint: passed
- Frontend production build: passed
- Backend compile check: passed

## Priority Improvements

### High

1. Add authentication and authorization before exposing the API beyond localhost. File write/delete and Git stage/commit endpoints can mutate the workspace; a client-supplied confirmation flag is not an authorization boundary.
2. Define an explicit consistency policy for document records, SQL chunks, and Qdrant vectors. Current embedding failures can leave a document reported as uploaded but unavailable to RAG, and vector deletion failures can leave stale retrieval results.

### Medium

3. Bound extracted document output and processing time, not only upload bytes. PDFs and DOCX files can expand significantly during parsing.
4. Make health-check semantics explicit for deployment. Return an appropriate non-2xx status for an unhealthy service, and distinguish required dependencies from optional Qdrant/Ollama services.
5. Replace direct JSON settings rewrites with an atomic write strategy, or make the database-backed settings repository the single persistence path.
6. Use one application version source for FastAPI metadata, health responses, documentation, and release notes.

### Low

7. Remove the standalone `backend/test_qdrant.py` smoke functions from normal pytest collection or convert their returned values into assertions; they currently generate pytest warnings and can attempt remote service calls during the default suite.
8. Replace deprecated Starlette status constants and update the TestClient/httpx dependency pairing.
9. Add failure-path tests for unavailable Qdrant, partial document indexing, parser resource limits, CORS disabled behavior, and interrupted settings writes.

## Working Tree Note

Runtime JSON/database files and dataset output were already modified or generated in the working tree during local use and test execution. They are intentionally not included in the maintenance commit.