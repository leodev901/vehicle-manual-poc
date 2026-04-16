from supabase import create_async_client, AsyncClient

from app.core.config import settings
from app.base.logger import logger

SUPABASE_URL = settings.SUPABASE_URL
SUPABASE_KEY = settings.SUPABASE_KEY

async def create_supabase_client() -> AsyncClient:
    """Supabase client 생성"""
    logger.info("create Supabse client")
    return await create_async_client(SUPABASE_URL, SUPABASE_KEY)


from fastapi import Request

async def get_supabase_client(request: Request) -> AsyncClient:
    """
    Request 객체에서 app.state에 저장된 supabase 비동기 클라이언트를 추출하여 반환합니다.
    """
    return request.app.state.supabase
