"""Campaign planning endpoints backed by the governed LangGraph workflow."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from signalscope.api.container import ApplicationContainer
from signalscope.api.dependencies import get_container
from signalscope.domain.models import CampaignRequest, DecisionBrief

router = APIRouter(prefix="/api/v1/campaigns", tags=["campaigns"])


@router.post("/plan", response_model=DecisionBrief, status_code=status.HTTP_201_CREATED)
def plan_campaign(
    request: CampaignRequest,
    container: ApplicationContainer = Depends(get_container),
) -> DecisionBrief:
    """Run the end-to-end workflow and retain an approval-ready output."""

    result = container.workflow.run(request)
    return container.workflows.save(result)


@router.get("/{workflow_id}", response_model=DecisionBrief)
def get_campaign(
    workflow_id: str,
    container: ApplicationContainer = Depends(get_container),
) -> DecisionBrief:
    """Retrieve a previous decision brief for dashboard refreshes or approvals."""

    result = container.workflows.get(workflow_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' was not found or has expired.",
        )
    return result


@router.get("", response_model=list[DecisionBrief])
def list_recent_campaigns(
    container: ApplicationContainer = Depends(get_container),
) -> list[DecisionBrief]:
    """Return recent workflow outputs in reverse chronological order."""

    return container.workflows.list_recent()
