from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.auth.dependencies import require_dashboard_access
from app.dependencies import get_observability_service
from app.services.observability_service import ObservabilityService

router = APIRouter(dependencies=[Depends(require_dashboard_access)])


@router.get("/summary")
async def get_observability_summary(
    brand_slug: str | None = Query(None),
    agent_id: str | None = Query(None),
    range_hours: int = Query(24, ge=1, le=720),
    service: ObservabilityService = Depends(get_observability_service),
):
    return await service.summarize(
        brand_slug=brand_slug,
        agent_id=agent_id,
        range_hours=range_hours,
    )
