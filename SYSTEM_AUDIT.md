# System Audit

Date: 2026-08-27

## Security Review - 2026-08-27

Current ratings:

- Overall engineering maturity: **6/10**
- Security for single-user localhost use: **5/10**
- Security for shared or internet-facing deployment: **3/10**

The system has a solid early-stage FastAPI/Next.js/SQLAlchemy structure, password
hashing, signed access tokens, authenticated feature APIs, path validation, and
workspace-scoped resource migration. It is not yet ready for multi-user or
internet-facing deployment.

Confirmed risks requiring follow-up:

1. Registration grants the `admin` role when the submitted email matches
   `ADMIN_EMAIL`; this is not a secure admin bootstrap mechanism.
2. Document retrieval, chunk retrieval, search, and deletion use workspace scope
   without consistently enforcing document ownership. The intended private versus
   shared document policy must be made explicit and enforced in every service and
   Qdrant filter.
3. When enabled, workspace file and Git tools target the shared repository root.
   Per-workspace filesystem isolation or a sandbox is required before multi-user
   enablement.
4. Upload byte limits do not fully bound PDF/DOCX expansion, parsing time,
   embedding work, or concurrent processing.
5. Browser bearer tokens are stored in `localStorage`, and token revocation is
   process-local. HttpOnly cookie sessions or equivalent XSS protections plus
   durable revocation are needed for hosted deployment.
6. Rate limits and usage enforcement are process-local or race-prone and need
   shared, atomic enforcement for multi-worker deployment.
7. CORS and deployment defaults need production validation, TLS guidance, and
	reverse-proxy/process-manager hardening.

Security test gaps include same-workspace cross-user document access, admin
registration hijacking, concurrent usage-limit enforcement, upload expansion,
multi-process rate limiting, token exposure, and production CORS configuration.

## Security Hardening Backlog

The following items are now tracked as the next production security milestone:

1. Central authorization middleware
2. Workspace membership enforcement
3. Document ownership enforcement
4. Qdrant tenant filters
5. Path traversal protection
6. Workspace filesystem sandbox
7. Agent capability allowlist
8. Action-bound approvals
9. Secret isolation
10. Git safety policy
11. Upload/resource limits
12. Redis rate limiting
13. Secure session/token handling
14. Security audit logs
15. Security regression tests
16. Dependency/SAST scanning
17. Prompt-injection/RAG security tests
18. Production security configuration

These items align to the current risk register and should be treated as required before shared or internet-facing deployment.

## Verified Changes

- Dataset creation now supports output directories outside the repository, including temporary and external deployment directories.
- `ENABLE_CORS=false` now disables CORS middleware as configured.
- `MessageInput` remains compatible when model selector props are omitted.
- Frontend tests now match the current message bubble and chat empty/loading states.
- TypeScript keeps the `@/*` frontend alias without relying on deprecated `baseUrl`.
- Frontend test files are included in the TypeScript project so VS Code resolves Jest globals and aliases.
- Frontend test fixtures include the current Sidebar deletion callback contract.
- Phase 11 now includes request-scoped Chat and grounded Ask mode across sync/streaming backend paths and the chat composer.
- Both frontend chat helpers include the selected mode in their request payload.
- Phase 11 includes standalone session-scoped semantic document search with result previews and icon-based controls.
- Phase 11 includes grounded Study mode with explanations, key points, flashcards, quizzes, and study icons.
- Phase 11 includes grounded Plan mode with ordered steps, checkpoints, assumptions, and risks.
- Phase 11 includes Auto mode with task-aware Chat, Ask, Study, and Plan selection plus a Sparkles icon.
- Phase 11 includes a safe Agent-mode proposal flow with ordered steps, tool intent, and approval points; execution remains disabled pending authorization gates.
- Phase 11 now includes bounded read-only Agent execution for file reads, code analysis, and document search; side-effecting tools remain unavailable.
- The frontend API client exposes typed `runReadOnlyAgent` support for the safe Agent actions.
- The frontend API client exposes typed approval requests for future side-effect execution.
- Confirmed file and Git mutations now consume matching one-time approval tokens.
- Collection searches combine session and collection filters to preserve private document isolation.
- Approval tokens are not a complete authorization boundary; they are now bound to authenticated users, but workspace policy and sandboxing remain required.
- Non-auth hardening now bounds extracted documents and JSON uploads, limits dataset output size, uses atomic settings replacement, protects approval consumption with a lock, and disables credentialed wildcard CORS.
- Agent approval primitives now issue short-lived, action/target-bound tokens; side-effect execution remains disabled until mutation endpoints consume them.
- Qdrant retrieval now uses the current `query_points` API, with legacy fallback support; embedding dimension lookup uses the current SentenceTransformers method.
- Qdrant collection diagnostics now support current `CollectionInfo` objects without assuming a `.name` attribute.
- Qdrant retrieval uses configurable `QDRANT_SCORE_THRESHOLD` with a `0.25` default to avoid dropping relevant low-score matches.
- Live verification indexed one document, retrieved it at `32.1%` relevance, and removed the temporary test vector afterward.
- Named knowledge collections now persist in SQLite and can be selected for document uploads and searches.
- Learning preferences and session/collection study progress now persist locally and personalize Study mode prompts.
- Restart the backend after deployment to apply the collection schema migration and expose the new `/collections` routes.
- Backend authentication now provides registration, login, signed bearer tokens, and `/auth/me`.
- Session, chat/history, document, collection, and Qdrant retrieval access is owner-scoped for authenticated API requests.
- Existing SQLite databases receive compatible `owner_id` columns during startup initialization.
- Alembic now contains an initial PostgreSQL schema revision; new databases can use `alembic upgrade head`.
- PostgreSQL startup now requires the Alembic version table at the current head and no longer mutates schema with `create_all()` or ad-hoc `ALTER TABLE` statements.
- The configured `melo_ai` database was initialized previously, so it was safely marked with `alembic stamp head` rather than recreating its existing tables.
- Settings, study, training, agent, coding, Git, and approval endpoints now require authentication; approvals are user-bound.
- Weak or placeholder `MELO_AUTH_SECRET` values now fail closed instead of falling back to a predictable signing key.
- Database connection strings are redacted in initialization error and info logs, and API reload defaults to disabled.
- Frontend clears stored authentication and workspace tokens after a `401` response.
- `/auth/logout` now revokes the current bearer token for the running backend process, and the frontend exposes a shared Sign out control.
- Shared filesystem/Git and Agent file tools are disabled by default; trusted local development must explicitly set `ENABLE_WORKSPACE_TOOLS=true`.
- Configurable request limits now protect authenticated feature APIs and authentication; only the configured platform admin is exempt from normal request limits.
- Monthly token usage is tracked per user/workspace with configurable limits; the configured platform admin is exempt.
- Rate-limit state is intentionally in memory for local deployment; distributed quotas remain required for multi-instance production deployments.
- Chat retrieval accepts an optional collection scope and deduplicates retrieved chunks while returning document/chunk source metadata.
- Workspace and membership models now exist, default workspaces are created/backfilled, and `/workspaces` lists authenticated memberships.
- Resource workspace migration `0003_resource_workspaces` is applied; existing sessions and documents are workspace-scoped, while multi-workspace membership and role policy remain unfinished.
- Study progress now validates the session workspace and persists/filter progress by workspace; Agent document search now propagates workspace scope.

## Validation

- Backend: not runnable in the current environment; pytest collection stops because
	the installed environment is missing `reportlab`, which is listed in
	`backend/requirements.txt`.
- Frontend: `37 passed`
- Static diagnostics: no errors reported
- Repository working tree: clean before documentation updates

## Priority Improvements

### High

1. Replace the local in-memory limiter with distributed rate limits and durable quotas for multi-instance deployment. File write/delete and Git stage/commit endpoints require explicit tool enablement but still target the shared server repository; per-workspace roots or sandboxing remain required before multi-user deployment.
2. Define an explicit consistency policy for document records, SQL chunks, and Qdrant vectors. Current embedding failures can leave a document reported as uploaded but unavailable to RAG, and vector deletion failures can leave stale retrieval results.

### Medium

3. Bound extracted document output and processing time, not only upload bytes. PDFs and DOCX files can expand significantly during parsing.
4. Make health-check semantics explicit for deployment. Return an appropriate non-2xx status for an unhealthy service, and distinguish required dependencies from optional Qdrant/Ollama services.
5. Replace direct JSON settings rewrites with an atomic write strategy, or make the database-backed settings repository the single persistence path.
6. Use one application version source for FastAPI metadata, health responses, documentation, and release notes.

### Low

7. Remove the SQLite compatibility `create_all()` path when SQLite support is no longer required.
8. Remove the standalone `backend/test_qdrant.py` smoke functions from normal pytest collection or convert their returned values into assertions; they currently generate pytest warnings and can attempt remote service calls during the default suite.
9. Replace deprecated Starlette status constants and update the TestClient/httpx dependency pairing.
10. Add failure-path tests for unavailable Qdrant, partial document indexing, parser resource limits, CORS disabled behavior, and interrupted settings writes.

### Token Revocation Note

Logout revocations are currently kept in process memory. Restarting the backend
clears the revocation set, so production deployments need a durable session or
token-revocation store plus refresh-token rotation.

## Working Tree Note

Runtime JSON/database files and dataset output were already modified or generated in the working tree during local use and test execution. They are intentionally not included in the maintenance commit.