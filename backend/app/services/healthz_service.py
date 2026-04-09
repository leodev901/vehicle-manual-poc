from supabase import Client
from fastapi import HTTPException

from app.schemas.healthz import HealthzRequest
from app.repositories.healthz_repository import HealthzRepository

class HealthzService:

    @staticmethod
    def health_check(
        payload: HealthzRequest,
        supabase: Client, 
    ):
        # schema = payload.schema or "vehicle_manual_rag"
        # table = payload.table  or "models"
        schema = payload.schema
        table = payload.table

        # DB작업은 repositories를 통해서 진행합니다.
        repo = HealthzRepository(supabase)
        data = repo.health_check(schema, table)
        if not data: 
            # 데이터가 없을 경우 HTTPException
            raise HTTPException(status_code=404, detail="Data not found")
        return data    
            