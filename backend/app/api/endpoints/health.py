from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from postgrest.exceptions import APIError

from app.core.dependencies import get_supabase_client
from app.base.logger import logger
from app.schemas.response import CommonResponse

from app.services.healthz_service import HealthzService
from app.schemas.healthz import HealthzRequest


api_router = APIRouter(tags=["health"])

@api_router.get("/health")
async def health():
    return CommonResponse.ok({"status": "ok"})

@api_router.get("/error")
async def error():
    return CommonResponse.error("Test Error")
    # raise ValueError("Test Error")
    # raise HTTPException(status_code=400, detail="Test Error")


@api_router.post("/healthz")
async def healthz(
    payload: HealthzRequest,
    supabase: Client = Depends(get_supabase_client),
):
    result = HealthzService.health_check(payload, supabase)
    return CommonResponse.ok(result)

    
