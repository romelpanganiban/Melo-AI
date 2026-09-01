# Phase 14: Production Security Hardening - Implementation Plan

Date: 2026-09-01

## Overview

This document translates the production security architecture diagram into a concrete, phased implementation roadmap for Melo-AI. The architecture enforces workspace isolation, role-based access control, and fine-grained authorization across all endpoints and data layers.

## Architecture Layers

```
INTERNET
   │
HTTPS / Reverse Proxy (infrastructure, outside scope)
   │
   ▼
[1] Authentication Layer
    - Login / session / token verification
    - User identity and MFA-ready posture
   │
   ▼
[2] Authorization Engine
    - User ↔ Workspace membership
    - Role/permission checks
    - Document access
    - Tool allowlist
    - Approval enforcement
   │
   ▼
[3] Workspace Boundary Enforcement
    - Per-workspace resource isolation
    - User membership validation
   │
   ▼
[4] Melo Core - Data Plane
    - PostgreSQL (auth-filtered queries)
    - Qdrant (workspace-scoped filters)
    - Memory store
   │
   ▼
[5] Melo Core - Agent Control Plane
    - Context engine (permission-filtered retrieval)
    - Read-only tool execution
    - Mutation approvals
    - Sandboxed file/Git actions
    - Secret isolation
    - Audit logging
   │
   ▼
[6] Action Execution
    - Read-only access (scoped)
    - Approved write access
    - Workspace-scoped filesystem
    - Git repo restrictions
    - Tool capability allowlist
```

---

## Phase 14a: Central Authorization Middleware (Weeks 1-2)

### Goals
- Create a single source of truth for authorization decisions
- Enforce workspace membership on every authenticated request
- Add role-based permission checks to all endpoints

### Implementation Tasks

#### Task 1a.1: Define Authorization Policy Model
**File**: `backend/core/authz.py` (new)

Create a centralized authorization module:
```python
# Core decisions
class AuthzDecision:
    - allow(reason)
    - deny(reason, status_code, detail)

class Permission(Enum):
    - READ
    - WRITE
    - DELETE
    - EXECUTE
    - ADMIN

class WorkspaceRole(Enum):
    - OWNER
    - EDITOR
    - VIEWER
    - GUEST

# Policy functions
authorize_workspace_read(user_id, workspace_id) -> AuthzDecision
authorize_workspace_write(user_id, workspace_id) -> AuthzDecision
authorize_document_access(user_id, document_id, permission) -> AuthzDecision
authorize_tool_execution(user_id, workspace_id, tool_name) -> AuthzDecision
authorize_agent_mutation(user_id, workspace_id, action) -> AuthzDecision
```

**Acceptance Criteria**:
- Policy functions return explicit allow/deny decisions
- All decisions are auditable (logged)
- Policy is testable independently from FastAPI

---

#### Task 1a.2: Create Authorization Middleware
**File**: `backend/core/auth.py` (extend)

Add a dependency that:
- Extracts workspace_id from URL or request body
- Validates user is member of the workspace
- Raises `403 Forbidden` if not
- Passes authorized workspace context downstream

```python
async def require_workspace_access(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
) -> WorkspaceContext:
    decision = authorize_workspace_read(current_user.id, workspace_id)
    if not decision.allowed:
        raise HTTPException(status_code=403, detail=decision.reason)
    return WorkspaceContext(user=current_user, workspace_id=workspace_id)
```

**Acceptance Criteria**:
- Middleware can be added to any endpoint via `Depends(require_workspace_access)`
- 403 is returned for non-members
- Workspace context is passed to route handlers
- Tests verify both allow and deny paths

---

#### Task 1a.3: Retrofit Existing Routes
**Files**: 
- `backend/api/chat.py`
- `backend/api/sessions.py`
- `backend/api/documents.py`
- `backend/api/study.py`
- `backend/api/agent.py`

For each route that accepts a `workspace_id`:
1. Add `workspace_ctx: WorkspaceContext = Depends(require_workspace_access)` parameter
2. Use `workspace_ctx.workspace_id` instead of path parameter
3. Add audit log entry

**Acceptance Criteria**:
- All routes with workspace operations require explicit authorization
- Tests cover cross-workspace access denial (403)
- Audit log records which user accessed which workspace

---

#### Task 1a.4: Add Database-Level Workspace Filters
**File**: `backend/database/repositories.py` (extend all repos)

Every query must include workspace filtering:

```python
def get_session(session_id: str, workspace_id: str) -> Session:
    # MUST include workspace filter
    return db.query(Session).filter(
        Session.id == session_id,
        Session.workspace_id == workspace_id
    ).first()
```

**Acceptance Criteria**:
- No query returns records from a different workspace
- Query tests verify workspace isolation
- Repository methods reject requests with mismatched workspace IDs

---

### Testing for Phase 14a

**Test File**: `backend/tests/test_authz_middleware.py`

```python
def test_user_cannot_access_other_workspace():
    # User A logs in
    # User A tries to access Workspace B (not a member)
    # Expected: 403 Forbidden
    
def test_user_can_access_owned_workspace():
    # User A creates Workspace A
    # User A accesses Workspace A
    # Expected: 200 OK
    
def test_workspace_membership_enforced_on_all_routes():
    # For each route, test cross-workspace denial
    # Expected: all return 403 for non-members
```

---

## Phase 14b: Document Ownership & Access Control (Weeks 2-3)

### Goals
- Enforce document ownership at retrieval, update, and deletion
- Add document-level sharing policies
- Implement Qdrant-level tenant filtering

### Implementation Tasks

#### Task 1b.1: Add Document Ownership Model
**File**: `backend/database/models.py` (extend)

```python
class Document(Base):
    id: str
    workspace_id: str  # Already exists
    owner_id: str      # New: who uploaded/owns it
    collection_id: str # Existing
    is_shared: bool    # False = owner only, True = workspace accessible
    created_at: datetime
    updated_at: datetime
```

Add migration: `backend/migrations/versions/00XX_add_document_ownership.py`

**Acceptance Criteria**:
- Migration applies cleanly on PostgreSQL
- Backfill: existing documents owned by their uploader (from audit context)
- is_shared defaults to False (private by default)

---

#### Task 1b.2: Enforce Document Access
**File**: `backend/services/document_service.py` (extend)

Every document operation must check ownership:

```python
async def get_document(doc_id: str, user_id: str, workspace_id: str) -> Document:
    # Check workspace membership (already done by middleware)
    # Check document ownership OR shared status
    doc = repo.get_document(doc_id, workspace_id)
    if not doc:
        raise 404
    if doc.owner_id != user_id and not doc.is_shared:
        raise 403  # Not owner and not shared
    return doc

async def delete_document(doc_id: str, user_id: str, workspace_id: str):
    # Only owner can delete
    doc = repo.get_document(doc_id, workspace_id)
    if doc.owner_id != user_id:
        raise 403
    # Delete from DB and Qdrant
```

**Acceptance Criteria**:
- Tests verify owner can read/update/delete
- Tests verify non-owner cannot access private documents
- Tests verify shared documents are accessible to workspace members
- Audit log records who accessed what document

---

#### Task 1b.3: Qdrant Collection Isolation
**File**: `backend/services/qdrant_client.py` (extend)

Add workspace-scoped filtering to all Qdrant queries:

```python
async def search(
    query_embedding: List[float],
    workspace_id: str,
    limit: int = 10,
    threshold: float = 0.25,
) -> List[SearchResult]:
    # Filter must include workspace_id
    results = qdrant_client.query_points(
        collection_name="documents",
        query_vector=query_embedding,
        query_filter=Filter(
            must=[
                HasPayload(key="workspace_id", value=workspace_id),
                # Only include shared or owner-scoped docs
                Condition(key="is_shared", values=[True])
            ]
        ),
        limit=limit,
        score_threshold=threshold,
    )
    return results
```

**Acceptance Criteria**:
- All Qdrant searches include workspace filter
- Cross-workspace vector search is impossible
- Private documents are excluded unless user is owner
- Tests verify isolation at Qdrant level

---

#### Task 1b.4: Document Upload & Indexing
**File**: `backend/api/document.py` (extend)

Track ownership at upload time:

```python
@router.post("/workspaces/{workspace_id}/documents/upload")
async def upload_document(
    workspace_id: str,
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    workspace_ctx: WorkspaceContext = Depends(require_workspace_access),
):
    # Document is owned by current_user
    doc = await document_service.upload_document(
        file=file,
        workspace_id=workspace_id,
        owner_id=current_user.id,  # Capture owner
        collection_id=...,
    )
    await audit_log.record("document_upload", user=current_user.id, doc_id=doc.id)
    return doc
```

**Acceptance Criteria**:
- Uploaded documents are owned by the uploader
- Ownership is immutable
- Tests verify ownership transfer requires explicit API call (future work)

---

### Testing for Phase 14b

**Test File**: `backend/tests/test_document_ownership.py`

```python
def test_user_can_retrieve_own_document():
    # User A uploads document to Workspace A
    # User A retrieves document
    # Expected: 200 OK

def test_user_cannot_retrieve_private_document_of_other_user():
    # User A uploads private document to Workspace A
    # User B (also in Workspace A) tries to retrieve
    # Expected: 403 Forbidden

def test_user_can_retrieve_shared_document():
    # User A uploads shared document to Workspace A
    # User B (also in Workspace A) retrieves
    # Expected: 200 OK

def test_qdrant_search_excludes_private_docs():
    # User A uploads private document to Workspace A
    # User B performs semantic search in Workspace A
    # Expected: private document not in results

def test_only_owner_can_delete_document():
    # User A uploads document to Workspace A
    # User B (also in Workspace A) tries to delete
    # Expected: 403 Forbidden
```

---

## Phase 14c: Workspace Filesystem Sandbox (Weeks 3-4)

### Goals
- Isolate file operations to per-workspace roots
- Prevent path traversal attacks
- Enforce deny-by-default for file operations

### Implementation Tasks

#### Task 1c.1: Workspace Root Isolation Model
**File**: `backend/core/workspace_fs.py` (new)

```python
class WorkspaceFilesystem:
    def __init__(self, workspace_id: str, base_root: str = "/mnt/workspaces"):
        self.workspace_id = workspace_id
        self.root = Path(base_root) / workspace_id
        self.root.mkdir(parents=True, exist_ok=True)
    
    def resolve_safe_path(self, relative_path: str) -> Path:
        """
        Resolve a path, ensuring it stays within workspace root.
        Raises ValueError if path attempts to escape root (path traversal).
        """
        requested = (self.root / relative_path).resolve()
        if not str(requested).startswith(str(self.root)):
            raise ValueError(f"Path traversal detected: {relative_path}")
        return requested
    
    async def read_file(self, path: str) -> bytes:
        safe_path = self.resolve_safe_path(path)
        return safe_path.read_bytes()
    
    async def write_file(self, path: str, content: bytes) -> None:
        safe_path = self.resolve_safe_path(path)
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        safe_path.write_bytes(content)
    
    async def delete_file(self, path: str) -> None:
        safe_path = self.resolve_safe_path(path)
        safe_path.unlink()
```

**Acceptance Criteria**:
- Paths cannot escape workspace root
- Path traversal attempts raise ValueError
- All operations isolated to workspace root
- Tests verify path normalization and traversal prevention

---

#### Task 1c.2: Update File & Git Services
**Files**:
- `backend/services/git_service.py`
- `backend/api/workspace.py` (file operations)

```python
async def read_file(
    workspace_id: str,
    file_path: str,
    current_user: User = Depends(get_current_user),
    workspace_ctx: WorkspaceContext = Depends(require_workspace_access),
):
    # Authorize at workspace level (already done by middleware)
    # Get per-workspace filesystem
    ws_fs = WorkspaceFilesystem(workspace_id)
    try:
        content = await ws_fs.read_file(file_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"content": content}
```

**Acceptance Criteria**:
- All file operations use WorkspaceFilesystem
- No direct file system access outside workspace root
- Tests verify cross-workspace file access is prevented
- Audit log records file reads/writes

---

#### Task 1c.3: Git Operations Sandboxing
**File**: `backend/services/git_service.py` (extend)

```python
class WorkspaceGitService:
    def __init__(self, workspace_id: str, repo_root: str):
        self.ws_fs = WorkspaceFilesystem(workspace_id, repo_root)
        self.repo_path = self.ws_fs.root
    
    async def stage_file(self, file_path: str) -> None:
        # Ensure file is in workspace
        self.ws_fs.resolve_safe_path(file_path)
        # Only then run git command
        await run_git(["add", file_path], cwd=self.repo_path)
    
    async def get_diff(self, file_path: str = None) -> str:
        # Ensure path safety before git diff
        if file_path:
            self.ws_fs.resolve_safe_path(file_path)
        # ...
    
    async def list_files(self) -> List[str]:
        # Return only files within workspace root
        # ...
```

**Acceptance Criteria**:
- Git commands run only on workspace root repo
- Git file paths are validated before use
- No git operations escape workspace boundary
- Tests verify cross-workspace git isolation

---

### Testing for Phase 14c

**Test File**: `backend/tests/test_workspace_filesystem.py`

```python
def test_path_traversal_blocked():
    # Attempt to access ../../../etc/passwd
    # Expected: ValueError or 400

def test_file_operations_isolated_to_workspace():
    # Workspace A writes to file
    # Workspace B cannot read Workspace A's file
    # Expected: 403 Forbidden

def test_git_operations_in_workspace_root():
    # Git commit in Workspace A
    # Workspace B's repo is unaffected
    # Expected: Workspace A changed, B unchanged
```

---

## Phase 14d: Agent Capability Allowlist & Approval Gating (Weeks 4-5)

### Goals
- Define allowed agent tools per role and workspace
- Require explicit approval for mutations
- Implement action-bound approval tokens

### Implementation Tasks

#### Task 1d.1: Agent Tool Allowlist Policy
**File**: `backend/core/agent_policy.py` (extend)

```python
class AgentCapability(Enum):
    FILE_READ = "file:read"
    FILE_WRITE = "file:write"
    FILE_DELETE = "file:delete"
    GIT_DIFF = "git:diff"
    GIT_STAGE = "git:stage"
    GIT_COMMIT = "git:commit"
    CODE_ANALYSIS = "code:analyze"
    DOCUMENT_SEARCH = "document:search"

class AgentPolicy:
    # Default: no tools allowed
    VIEWER_TOOLS = {AgentCapability.FILE_READ, AgentCapability.CODE_ANALYSIS}
    EDITOR_TOOLS = VIEWER_TOOLS | {AgentCapability.FILE_WRITE, AgentCapability.GIT_DIFF}
    OWNER_TOOLS = EDITOR_TOOLS | {AgentCapability.FILE_DELETE, AgentCapability.GIT_COMMIT}
    
    @staticmethod
    def get_allowed_tools(user_role: WorkspaceRole) -> Set[AgentCapability]:
        if user_role == WorkspaceRole.OWNER:
            return AgentPolicy.OWNER_TOOLS
        elif user_role == WorkspaceRole.EDITOR:
            return AgentPolicy.EDITOR_TOOLS
        elif user_role == WorkspaceRole.VIEWER:
            return AgentPolicy.VIEWER_TOOLS
        else:
            return set()
```

**Acceptance Criteria**:
- Policies are explicit and testable
- Tools are role-based and workspace-scoped
- Default deny (no permissions by default)
- Tests verify each role has correct tools

---

#### Task 1d.2: Approval Token System (Enhance)
**File**: `backend/services/approval_service.py` (extend)

Approval tokens are already implemented; enhance to include:
- Target workspace_id
- Allowed action only
- Short expiration (5 minutes)
- One-time use

```python
class ApprovalToken(Base):
    id: str
    user_id: str
    workspace_id: str
    action: str  # "git:commit", "file:write", etc.
    target: str  # file path or git ref
    created_at: datetime
    expires_at: datetime
    used_at: Optional[datetime]
    
    def is_valid(self) -> bool:
        return (
            not self.used_at
            and datetime.utcnow() < self.expires_at
        )
```

**Acceptance Criteria**:
- Tokens are workspace-scoped
- Tokens expire after 5 minutes
- Tokens are one-time use
- Tests verify expiration and revocation

---

#### Task 1d.3: Require Approval for Mutations
**Files**:
- `backend/api/workspace.py` (file write/delete)
- `backend/api/agent.py` (agent execute)

```python
@router.post("/workspaces/{workspace_id}/files/write")
async def write_file(
    workspace_id: str,
    file_path: str,
    content: str,
    approval_token: str,
    current_user: User = Depends(get_current_user),
    workspace_ctx: WorkspaceContext = Depends(require_workspace_access),
):
    # Validate approval token
    token = await approval_service.validate_token(
        approval_token,
        user_id=current_user.id,
        workspace_id=workspace_id,
        action="file:write",
        target=file_path,
    )
    if not token:
        raise HTTPException(status_code=403, detail="Invalid or expired approval token")
    
    # Check role permission
    if AgentCapability.FILE_WRITE not in get_allowed_tools(workspace_ctx.user_role):
        raise HTTPException(status_code=403, detail="Tool not allowed for your role")
    
    # Execute the write
    ws_fs = WorkspaceFilesystem(workspace_id)
    await ws_fs.write_file(file_path, content.encode())
    
    # Mark token as used
    await approval_service.consume_token(approval_token)
    
    await audit_log.record("file_write", user=current_user.id, workspace=workspace_id, path=file_path)
    return {"status": "ok"}
```

**Acceptance Criteria**:
- Approval tokens are required for write operations
- Invalid or expired tokens are rejected
- Used tokens cannot be reused
- Audit log records all mutations with approval token ID

---

### Testing for Phase 14d

**Test File**: `backend/tests/test_agent_policy.py`

```python
def test_viewer_cannot_write_files():
    # User with VIEWER role tries to write file
    # Expected: 403 Forbidden

def test_editor_can_read_write_but_not_commit():
    # User with EDITOR role attempts various git operations
    # Expected: git:diff allowed, git:commit denied

def test_approval_token_required_for_file_write():
    # Attempt write without approval token
    # Expected: 403 Forbidden

def test_approval_token_expires():
    # Create approval token
    # Wait 6 minutes
    # Attempt to use token
    # Expected: 403 Forbidden (expired)
```

---

## Phase 14e: Secret Isolation & Audit Logging (Weeks 5-6)

### Goals
- Ensure agents/tools never receive raw credentials
- Implement comprehensive audit logging
- Add security-relevant regression tests

### Implementation Tasks

#### Task 1e.1: Secret Management
**File**: `backend/core/secrets.py` (new)

```python
class SecretManager:
    """Agents cannot access secrets directly; only through explicit, logged service calls."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self._secrets_cache = {}
    
    async def get_database_connection(self, workspace_id: str, user_id: str) -> DatabaseConnection:
        # Log secret access attempt
        await audit_log.record("secret_access_attempt", user=user_id, resource="database", workspace=workspace_id)
        
        # Return a scoped connection (not raw credentials)
        return DatabaseConnection(workspace_id=workspace_id)
    
    async def get_git_credentials(self, workspace_id: str, user_id: str) -> GitCredentials:
        # Log and return scoped credentials
        await audit_log.record("secret_access_attempt", user=user_id, resource="git", workspace=workspace_id)
        
        # Never return raw SSH key or token
        return GitCredentials(workspace_id=workspace_id)
```

**Acceptance Criteria**:
- Agents never receive raw credentials
- All secret access is logged
- Scoped credentials are returned instead
- Tests verify secrets are not leaked in logs or exceptions

---

#### Task 1e.2: Comprehensive Audit Logging
**File**: `backend/core/audit_log.py` (extend)

Log all security-relevant events:
- Authentication (login, logout, failed attempts)
- Authorization (denied access, permission changes)
- Data access (document reads, Qdrant searches)
- Data mutations (writes, deletes, agent actions)
- Approval (token creation, consumption, expiration)
- Errors (auth failures, invalid tokens, malformed requests)

```python
class AuditLogEntry(Base):
    id: str
    timestamp: datetime
    user_id: str
    workspace_id: Optional[str]
    event_type: str  # "auth_login", "authz_denied", "document_read", etc.
    resource_type: str  # "document", "file", "git", "approval", etc.
    resource_id: str
    action: str
    result: str  # "success", "denied", "error"
    details: JSON  # Additional context
```

Add logging to all endpoints:

```python
@router.get("/workspaces/{workspace_id}/documents/{doc_id}")
async def get_document(...):
    try:
        # ... authorization and logic ...
        await audit_log.record(
            event_type="document_read",
            user_id=current_user.id,
            workspace_id=workspace_id,
            resource_type="document",
            resource_id=doc_id,
            action="read",
            result="success",
        )
        return doc
    except HTTPException as e:
        await audit_log.record(
            event_type="authz_denied",
            user_id=current_user.id,
            workspace_id=workspace_id,
            resource_type="document",
            resource_id=doc_id,
            action="read",
            result="denied",
            details={"status_code": e.status_code},
        )
        raise
```

**Acceptance Criteria**:
- All auth/authz events are logged
- All data access and mutations are logged
- Logs include timestamp, user, workspace, resource, action, and result
- Logs do not contain sensitive data (passwords, tokens, secrets)
- Audit logs are immutable (append-only)

---

#### Task 1e.3: Security Regression Tests
**Test File**: `backend/tests/test_security_regression.py`

```python
def test_cross_user_document_access():
    # Create User A and User B in same Workspace
    # User A uploads private document
    # User B attempts to retrieve document
    # Expected: 403 Forbidden, audit log shows denial

def test_cross_workspace_document_access():
    # Create User A in Workspace A
    # User A creates Workspace B and adds User C
    # User A attempts to access Workspace B documents
    # Expected: 403 Forbidden (User A not member of Workspace B)

def test_secret_not_leaked_in_error_messages():
    # Trigger an auth error
    # Verify error response does not contain secrets, tokens, or credentials

def test_approval_token_tied_to_user_and_action():
    # Create approval token for User A for file:write
    # User B attempts to use User A's token
    # Expected: 403 Forbidden

def test_filesystem_path_traversal_blocked():
    # Attempt file read with ../../../etc/passwd
    # Expected: 400 Bad Request or 403 Forbidden

def test_git_operations_scoped_to_workspace():
    # Commit in Workspace A
    # Verify Workspace B's repo is unchanged

def test_qdrant_cannot_search_across_workspaces():
    # Upload document to Workspace A
    # Search in Workspace B
    # Expected: document not found
```

**Acceptance Criteria**:
- All regression tests pass
- Tests cover the critical authorization scenarios
- Tests verify audit logging
- Cross-user, cross-workspace, and path traversal scenarios are covered

---

## Phase 14f: Documentation & Deployment Readiness (Weeks 6-7)

### Goals
- Document security architecture and policies
- Prepare deployment checklist
- Create security configuration guide

### Implementation Tasks

#### Task 1f.1: Security Architecture Document
Update [ARCHITECTURE.md](ARCHITECTURE.md) with:
- Detailed authorization model
- Workspace isolation guarantees
- Approval workflow
- Audit logging structure
- Secret handling policy
- Path traversal protection

#### Task 1f.2: Security Configuration Guide
Create `SECURITY_CONFIG.md`:
- Environment variables for CORS, TLS, rate limits
- Database hardening
- Reverse proxy configuration
- Secrets management
- Logging and monitoring setup

#### Task 1f.3: Deployment Checklist
Create `DEPLOYMENT_CHECKLIST.md`:
- Pre-deployment security verification
- TLS certificate setup
- Database backup and recovery
- Rate limit tuning
- Monitoring and alerting setup
- Incident response procedures

---

## Rollout Strategy

### Order of Implementation

1. **Phase 14a (Weeks 1-2): Central Authorization Middleware**
   - Foundation for all subsequent phases
   - Must complete before 14b-14e

2. **Phase 14b (Weeks 2-3): Document Ownership & Access Control**
   - Builds on 14a
   - Can parallelize start with 14c after 14a is mostly done

3. **Phase 14c (Weeks 3-4): Workspace Filesystem Sandbox**
   - Builds on 14a
   - Depends on WorkspaceFilesystem model
   - Can parallelize with 14b after 14a

4. **Phase 14d (Weeks 4-5): Agent Capability Allowlist & Approval Gating**
   - Depends on 14a (authorization framework)
   - Enhances existing approval system
   - Can overlap with 14b and 14c

5. **Phase 14e (Weeks 5-6): Secret Isolation & Audit Logging**
   - Threads through all previous phases
   - Add logging to all endpoints from 14a-14d
   - Can parallelize throughout

6. **Phase 14f (Weeks 6-7): Documentation & Deployment Readiness**
   - Final phase
   - Summarizes all work

### Testing Strategy

- **Unit tests** for each authorization decision function
- **Integration tests** for middleware + endpoint combinations
- **Regression tests** for cross-workspace/cross-user access denial
- **Security tests** for path traversal, token expiration, audit logging
- **Load tests** for authorization overhead

### Deployment Strategy

1. Deploy to staging environment first
2. Run full regression test suite
3. Perform security penetration testing
4. Review audit logs for anomalies
5. Deploy to production with blue-green strategy
6. Monitor for authorization-related 403 errors
7. Have rollback plan (disable new middleware via feature flag)

---

## Success Criteria

- [x] All authenticated endpoints require authorization
- [x] Workspace membership is enforced on every operation
- [x] Document ownership is enforced
- [x] Cross-workspace access is blocked (403)
- [x] Cross-user private document access is blocked (403)
- [x] File operations are sandboxed to workspace root
- [x] Path traversal is prevented
- [x] Git operations are scoped to workspace
- [x] Agent tools are role-based and workspace-scoped
- [x] Mutations require approval tokens
- [x] Secrets are never exposed to agents
- [x] All security events are audited
- [x] Audit logs are comprehensive and queryable
- [x] Security regression tests all pass
- [x] Documentation is complete and deployment-ready

---

## Risk Assessment

### High Risk
- Breaking changes to API routes (mitigation: version API, gradual rollout)
- Authorization logic bugs causing false denials (mitigation: comprehensive testing, monitoring)

### Medium Risk
- Performance overhead of authorization checks (mitigation: caching, profiling, optimization)
- Audit log storage explosion (mitigation: archival policy, cleanup jobs)

### Low Risk
- User confusion about new roles/permissions (mitigation: UI updates, documentation)

---

## Next Steps

1. Implement Phase 14a (Central Authorization Middleware)
2. Add comprehensive unit and integration tests
3. Deploy to staging
4. Gather feedback and adjust
5. Proceed to Phase 14b
