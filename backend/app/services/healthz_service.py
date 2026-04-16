
from fastapi import HTTPException, Depends

from app.schemas.healthz import HealthzRequest
from app.repositories.health.protocol import HealthzRepositoryProtocol


class HealthzService:
    def __init__(
        self, 
        health_repository:  HealthzRepositoryProtocol
    ):
        self.health_repository = health_repository

    async def health_check(
        self,
        payload: HealthzRequest,
    ):
        # schemas 에서 field_validator 에서 초기화를했기 때문에 None으로 들어오지 않음
        schema_name = payload.schema_name
        table_name = payload.table_name

        # DB작업은 repositories를 통해서 진행합니다.
        data = await self.health_repository.health_check(schema_name, table_name)
        if not data: 
            # 데이터가 없을 경우 HTTPException
            raise HTTPException(status_code=404, detail="Data not found")
        return data
            