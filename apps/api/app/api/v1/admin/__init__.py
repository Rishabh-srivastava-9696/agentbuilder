from fastapi import APIRouter
from .brands import router as brands_router
from .agents import router as agents_router

router = APIRouter()

router.include_router(brands_router, prefix="/brands", tags=["brands"])
router.include_router(agents_router, prefix="/agents", tags=["agents"])
