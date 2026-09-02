"""Admin API for data reconciliation and system health operations."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.auth import get_current_user, require_admin
from database import get_db
from database.models import User
from services.reconciliation_service import get_reconciliation_service
from core.logging import logger, audit_log

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/reconciliation/audit", status_code=status.HTTP_200_OK)
def audit_reconciliation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Audit SQL and Qdrant for inconsistencies (read-only).
    
    Requires admin authentication.
    
    Returns:
        Report of findings without making changes
    """
    require_admin(current_user.id, db)
    
    try:
        logger.info("Admin reconciliation audit initiated", extra={"user_id": current_user.id})
        audit_log("admin.reconciliation.audit", user_id=str(current_user.id), outcome="success")
        service = get_reconciliation_service()
        report = service.audit()
        return report.to_dict()
    except Exception as e:
        logger.error(f"Reconciliation audit failed: {str(e)}", extra={"user_id": current_user.id})
        audit_log("admin.reconciliation.audit", user_id=str(current_user.id), outcome="error", reason=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reconciliation audit failed: {str(e)}"
        )


@router.post("/reconciliation/repair", status_code=status.HTTP_200_OK)
def repair_reconciliation(
    missing_embeddings: bool = True,
    delete_orphaned: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Repair SQL/Qdrant inconsistencies.
    
    Requires admin authentication.
    
    Args:
        missing_embeddings: If true, re-generate missing embeddings
        delete_orphaned: If true, delete orphaned vectors from Qdrant (DANGEROUS!)
    
    Returns:
        Report of repairs performed
    """
    require_admin(current_user.id, db)
    
    # Safety guard for delete_orphaned
    if delete_orphaned:
        logger.warning(
            "Admin requested orphaned vector deletion",
            extra={"user_id": current_user.id}
        )
    
    try:
        logger.info(
            "Admin reconciliation repair initiated",
            extra={
                "user_id": current_user.id,
                "missing_embeddings": missing_embeddings,
                "delete_orphaned": delete_orphaned
            }
        )
        audit_log(
            "admin.reconciliation.repair",
            user_id=str(current_user.id),
            missing_embeddings=missing_embeddings,
            delete_orphaned=delete_orphaned,
            outcome="success",
        )
        service = get_reconciliation_service()
        report = service.repair(
            missing_embeddings=missing_embeddings,
            delete_orphaned=delete_orphaned
        )
        return report.to_dict()
    except Exception as e:
        logger.error(f"Reconciliation repair failed: {str(e)}", extra={"user_id": current_user.id})
        audit_log(
            "admin.reconciliation.repair",
            user_id=str(current_user.id),
            missing_embeddings=missing_embeddings,
            delete_orphaned=delete_orphaned,
            outcome="error",
            reason=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reconciliation repair failed: {str(e)}"
        )
