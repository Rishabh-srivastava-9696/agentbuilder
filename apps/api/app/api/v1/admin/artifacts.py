from __future__ import annotations

from fastapi import APIRouter, Depends

from app.auth.dependencies import require_dashboard_access
from app.services.artifact_registry import list_artifact_types


router = APIRouter(dependencies=[Depends(require_dashboard_access)])


@router.get("", include_in_schema=False)
@router.get("/")
async def list_built_in_artifact_types():
    """Built-in chat artifact types the admin can enable per agent."""
    return {"artifacts": list_artifact_types()}
