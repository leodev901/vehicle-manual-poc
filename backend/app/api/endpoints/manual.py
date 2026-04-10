from fastapi import APIRouter, Depends, Query
from pydantic import Field

from app.schemas.response import CommonResponse
from app.services.manual_service import ManualService



api_router = APIRouter(prefix="/api/v1/manual",tags=["manual"])

@api_router.get("/brands")
async def list_brands(
    service: ManualService = Depends(ManualService),
):
    resp = await service.list_brands()
    return CommonResponse.ok(data=resp)

@api_router.get("/lineups")
async def list_lineups(
    brand_id: str = Query(...,description="Brand ID", example="HD"),
    service: ManualService = Depends(ManualService),
):
    resp = await service.list_lineups(brand_id)
    return CommonResponse.ok(data=resp)

@api_router.get("/models")
async def list_models(
    lineup_id: str = Query(...,description="Lineup ID", example="LX3"),
    service: ManualService = Depends(ManualService),
):
    resp = await service.list_models(lineup_id)
    return CommonResponse.ok(data=resp)


