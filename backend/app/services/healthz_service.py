from supabase import AsyncClient
from fastapi import HTTPException, Depends

from app.schemas.healthz import HealthzRequest
from app.repositories.healthz_repository import HealthzRepository
from app.core.dependencies import get_supabase_client

class HealthzService:
    def __init__(self, supabase: AsyncClient = Depends(get_supabase_client)):
        self.supabase = supabase

    async def health_check(
        self,
        payload: HealthzRequest,
    ):
        # schemas 에서 field_validator 에서 초기화를했기 때문에 None으로 들어오지 않음
        schema_name = payload.schema_name
        table_name = payload.table_name

        # DB작업은 repositories를 통해서 진행합니다.
        repo = HealthzRepository(self.supabase)
        data = await repo.health_check(schema_name, table_name)
        if not data: 
            # 데이터가 없을 경우 HTTPException
            raise HTTPException(status_code=404, detail="Data not found")
        return data
            