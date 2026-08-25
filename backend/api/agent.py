"""Safe read-only Agent mode actions."""

from typing import Literal, Optional

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from core.errors import ChatServiceError, ValidationError
from core.validation import validate_uuid
from services.code_analysis_service import get_code_analysis_service
from services.document_service import DocumentService
from services.approval_service import get_approval_service
from core.auth import get_current_user

router = APIRouter()
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


class ApprovalRequest(BaseModel):
    action: Literal["write_file", "delete_file", "git_stage", "git_commit"]
    target: str = Field(..., min_length=1, max_length=1000)


@router.post("/agent/approvals", status_code=status.HTTP_201_CREATED)
def create_approval(request: ApprovalRequest, user=Depends(get_current_user)):
    """Issue a short-lived approval token for a specific side-effecting action."""
    return approval_service.create(request.action, request.target, owner_id=user.id)


@router.post("/agent/run", status_code=status.HTTP_200_OK)
def run_read_only_agent(request: AgentRunRequest, user=Depends(get_current_user)):
    """Execute bounded read-only actions; side-effecting actions are unsupported."""
    results = []
    try:
        for action in request.actions:
            if action.action == "read_file":
                if not action.path:
                    raise ValidationError("path is required", field="path")
                results.append({"action": action.action, "result": code_service.read_file(action.path)})
            elif action.action == "analyze_code":
                if not action.path:
                    raise ValidationError("path is required", field="path")
                results.append({"action": action.action, "result": code_service.analyze_file(action.path)})
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
                        owner_id=user.id,
                    ),
                })
        return {"results": results, "executed": len(results), "side_effects": False}
    except ValidationError:
        raise
    except Exception as exc:
        raise ChatServiceError("Agent action failed") from exc