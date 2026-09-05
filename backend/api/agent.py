"""Safe read-only Agent mode actions."""

from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from core.errors import ChatServiceError, ValidationError
from core.validation import validate_uuid
from services.code_analysis_service import get_code_analysis_service
from services.document_service import DocumentService
from services.approval_service import get_approval_service
from services.git_service import GitService
from core.auth import require_workspace_access_from_header, WorkspaceContext
from core.authz import AuthorizationPolicy, ToolCapability
from core.settings import settings
from core.logging import audit_log
from core.rate_limit import enforce_request_rate_limit
from database.connection import get_db
from sqlalchemy.orm import Session

router = APIRouter(dependencies=[Depends(enforce_request_rate_limit)])
code_service = get_code_analysis_service()
document_service = DocumentService()
approval_service = get_approval_service()


class AgentAction(BaseModel):
    action: Literal["read_file", "analyze_code", "search_documents"]
    path: Optional[str] = Field(None, max_length=500)
    query: Optional[str] = Field(None, max_length=2000)
    session_id: Optional[str] = None
    collection_id: Optional[str] = None


class AgentRunRequest(BaseModel):
    actions: list[AgentAction] = Field(..., min_length=1, max_length=5)


class AgentMutationRequest(BaseModel):
    action: Literal["write_file", "delete_file", "git_stage", "git_commit"]
    approval_id: str = Field(..., min_length=1, max_length=200)
    path: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = Field(None, max_length=1_000_000)
    paths: Optional[list[str]] = Field(None, min_length=1, max_length=50)
    message: Optional[str] = Field(None, max_length=500)


class ApprovalRequest(BaseModel):
    action: Literal["write_file", "delete_file", "git_stage", "git_commit"]
    target: str = Field(..., min_length=1, max_length=1000)


@router.post("/agent/approvals", status_code=status.HTTP_201_CREATED)
def create_approval(
    request: ApprovalRequest,
    workspace_ctx: WorkspaceContext = Depends(require_workspace_access_from_header()),
):
    """Issue a short-lived approval token for a specific side-effecting action."""
    # Only owners and admins can create approval tokens
    if workspace_ctx.role.name not in ("OWNER", "ADMIN"):
        raise HTTPException(status_code=403, detail="Insufficient workspace role")
    return approval_service.create(request.action, request.target, owner_id=workspace_ctx.user.id, workspace_id=workspace_ctx.workspace_id)


@router.post("/agent/run", status_code=status.HTTP_200_OK)
def run_read_only_agent(
    request: AgentRunRequest,
    workspace_ctx: WorkspaceContext = Depends(require_workspace_access_from_header()),
    db: Session = Depends(get_db),
):
    """Execute bounded read-only actions; side-effecting actions are unsupported."""
    results = []
    try:
        policy = AuthorizationPolicy(db)
        capability_by_action = {
            "read_file": ToolCapability.FILE_READ,
            "analyze_code": ToolCapability.CODE_ANALYSIS,
            "search_documents": ToolCapability.DOCUMENT_SEARCH,
        }
        for action in request.actions:
            capability = capability_by_action[action.action]
            if capability.value not in settings.AGENT_ALLOWED_CAPABILITIES:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Agent capability {capability.value} is disabled",
                )
            decision = policy.authorize_tool_execution(
                workspace_ctx.user.id,
                workspace_ctx.workspace_id,
                capability,
            )
            if not decision.allowed:
                raise HTTPException(status_code=decision.status_code, detail=decision.reason)

            if action.action == "read_file":
                if not action.path:
                    raise ValidationError("path is required", field="path")
                results.append({
                    "action": action.action,
                    "result": code_service.with_workspace(workspace_ctx.workspace_id).read_file(action.path),
                })
            elif action.action == "analyze_code":
                if not action.path:
                    raise ValidationError("path is required", field="path")
                results.append({
                    "action": action.action,
                    "result": code_service.with_workspace(workspace_ctx.workspace_id).analyze_file(action.path),
                })
            elif action.action == "search_documents":
                if not action.query or not action.session_id:
                    raise ValidationError("query and session_id are required", field="action")
                session_id = validate_uuid(action.session_id, field_name="session_id")
                results.append({
                    "action": action.action,
                    "result": document_service.search_documents(
                        action.query,
                        session_id,
                        action.collection_id,
                        owner_id=workspace_ctx.user.id,
                        workspace_id=workspace_ctx.workspace_id,
                    ),
                })
        return {"results": results, "executed": len(results), "side_effects": False}
    except (HTTPException, ValidationError):
        raise
    except Exception as exc:
        raise ChatServiceError("Agent action failed") from exc


@router.post("/agent/mutate", status_code=status.HTTP_200_OK)
def run_agent_mutation(
    request: AgentMutationRequest,
    workspace_ctx: WorkspaceContext = Depends(require_workspace_access_from_header()),
    db: Session = Depends(get_db),
):
    """Execute one explicitly approved, workspace-scoped mutation."""
    if not settings.ENABLE_WORKSPACE_TOOLS:
        raise HTTPException(status_code=503, detail="Workspace tools are disabled")

    capability_by_action = {
        "write_file": ToolCapability.FILE_WRITE,
        "delete_file": ToolCapability.FILE_DELETE,
        "git_stage": ToolCapability.GIT_STAGE,
        "git_commit": ToolCapability.GIT_COMMIT,
    }
    capability = capability_by_action[request.action]
    target = request.path if request.action in ("write_file", "delete_file") else (
        "\n".join(request.paths or []) if request.action == "git_stage" else request.message
    )
    if not target:
        raise ValidationError("mutation target is required", field="target")

    try:
        policy = AuthorizationPolicy(db)
        if capability.value not in settings.AGENT_ALLOWED_CAPABILITIES:
            raise HTTPException(status_code=403, detail=f"Agent capability {capability.value} is disabled")

        decision = policy.authorize_tool_execution(
            workspace_ctx.user.id,
            workspace_ctx.workspace_id,
            capability,
        )
        if not decision.allowed:
            raise HTTPException(status_code=decision.status_code, detail=decision.reason)

        if not approval_service.consume_for_request(
            request.approval_id,
            request.action,
            target,
            owner_id=workspace_ctx.user.id,
            workspace_id=workspace_ctx.workspace_id,
            policy=policy,
        ):
            raise HTTPException(status_code=403, detail="Valid approval is required for this mutation")

        if request.action == "write_file":
            if request.content is None:
                raise ValidationError("content is required", field="content")
            result = code_service.with_workspace(workspace_ctx.workspace_id).write_file(
                request.path, request.content, confirm=True
            )
        elif request.action == "delete_file":
            result = code_service.with_workspace(workspace_ctx.workspace_id).delete_file(
                request.path, confirm=True
            )
        elif request.action == "git_stage":
            result = GitService(workspace_id=workspace_ctx.workspace_id).stage(request.paths or [], confirm=True)
        else:
            result = GitService(workspace_id=workspace_ctx.workspace_id).commit(request.message or "", confirm=True)

        audit_log(
            "agent.mutation.executed",
            user_id=str(workspace_ctx.user.id),
            workspace_id=workspace_ctx.workspace_id,
            action=request.action,
            target=target,
            outcome="success",
        )
        return {"action": request.action, "result": result, "side_effects": True}
    except (HTTPException, ValidationError):
        raise
    except Exception as exc:
        audit_log(
            "agent.mutation.failed",
            user_id=str(workspace_ctx.user.id),
            workspace_id=workspace_ctx.workspace_id,
            action=request.action,
            outcome="error",
            reason=str(exc),
        )
        raise ChatServiceError("Agent mutation failed") from exc