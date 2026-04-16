from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db_session

class HealthzSqlAlchemyRepository:
    def __init__(self, session: AsyncSession = Depends(get_db_session)):
        self.session = session

    async def health_check(self, schema_name:str, table_name:str):
        """요청 받은 '스미카'와 '테이블'의 데이터를 1건 조회 한다 -> health check"""
        resp = await self.session.execute(text(f"SELECT * FROM {schema_name}.{table_name} LIMIT 1"))
        data = resp.fetchone()

        # 조회된 데이터가 없으면 None을 리턴하고, 있으면 딕셔너리로 변환
        return dict(data._mapping) if data else None