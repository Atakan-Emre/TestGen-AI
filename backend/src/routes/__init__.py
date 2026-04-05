from fastapi import APIRouter
from .scenario_routes import router as scenario_router
from .bsc_routes import router as bsc_router

router = APIRouter()

router.include_router(scenario_router, prefix="/scenarios", tags=["scenarios"])
router.include_router(bsc_router, prefix="/tests/bsc", tags=["tests"]) 