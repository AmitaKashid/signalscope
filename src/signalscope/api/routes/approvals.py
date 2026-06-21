"""Human approval endpoints that preserve final editorial control."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from signalscope.api.container import ApplicationContainer
from signalscope.api.dependencies import get_container
from signalscope.domain.models import ApprovalRecord, ApprovalRequest

router = APIRouter(prefix="/api/v1/workflows", tags=["approvals"])


@router.post("/{workflow_id}/approval", response_model=ApprovalRecord)
def submit_approval(
    workflow_id: str,
    request: ApprovalRequest,
    container: ApplicationContainer = Depends(get_container),
) -> ApprovalRecord:
    """Record a reviewer decision only for an existing workflow."""

    if container.workflows.get(workflow_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' was not found.",
        )
    return container.approvals.record(workflow_id, request)


@router.get("/{workflow_id}/approval", response_model=ApprovalRecord)
def get_approval(
    workflow_id: str,
    container: ApplicationContainer = Depends(get_container),
) -> ApprovalRecord:
    """Return the most recent human approval decision."""

    approval = container.approvals.get(workflow_id)
    if approval is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No approval record exists for workflow '{workflow_id}'.",
        )
    return approval
