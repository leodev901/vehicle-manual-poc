from fastapi import HTTPException
from app.repositories.manual.protocol import ManualRepositoryProtocol


class ManualService:
    def __init__(
        self,
        manual_repository: ManualRepositoryProtocol,
    ):
        self.manual_repository = manual_repository

    async def list_brands(self):
        result = await self.manual_repository.list_brands()
        if not result or len(result) == 0:
            raise HTTPException(status_code=404, detail="차량 브랜드 정보를 찾을 수 없습니다.")
        return result

    async def list_lineups(self, brand_id:str):
        result = await self.manual_repository.list_lineups(brand_id)
        if not result or len(result) == 0:
            raise HTTPException(status_code=404, detail="차량 라인업 정보를 찾을 수 없습니다.")
        return result
    
    async def list_models(self, lineup_id:str):
        result = await self.manual_repository.list_models(lineup_id)
        if not result or len(result) == 0:
            raise HTTPException(status_code=404, detail="차량 모델 정보를 찾을 수 없습니다.")
        return result




            
        

        