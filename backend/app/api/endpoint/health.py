from fastapi import APIRouter, Depends
from supabase import Client

from app.core.dependencies import get_supabase_client
from app.base.logger import logger
from app.services.health_service import HealthCheckService
from app.schemas.response import CommonResponse




api_router = APIRouter(tags=["health"])

@api_router.get("/health")
async def health():
    return CommonResponse.ok({"status": "ok"})


@api_router.get("/healthz")
async def healthz(
    schema:str="vehicle_manual_rag",
    table:str="models",
    supabse:Client = Depends(get_supabase_client),
):
    try:
        result = HealthCheckService.health_check(supabse, schema, table)
        # return {"status": "ok", "data": result}
        return CommonResponse.ok(result)
    
    except Exception as e:
        logger.error(f"{type(e).__name__} - {e}")
        # return {"status": "error", "message": str(e)}
        CommonResponse.error(f"{type(e).__name__} - {e}")

    
