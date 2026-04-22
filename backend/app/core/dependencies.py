from fastapi import Request,Depends
from supabase import AsyncClient


# ============================================================================
# Repository Dependencies
# ============================================================================

async def get_supabase_client(request: Request) -> AsyncClient:
    """
    Request 객체에서 app.state에 저장된 supabase 비동기 클라이언트를 추출하여 반환합니다.
    """
    return request.app.state.supabase
 
async def get_llm_client(request: Request) -> dict:
    """
    Request 객체에서 app.state에 저장된 llm 클라이언트를 추출하여 반환합니다.
    """
    
    return request.app.state.llm

async def get_langchain_client(request: Request) -> dict:
    """
    Request 객체에서 app.state에 저장된 langchain 클라이언트를 추출하여 반환합니다.
    """
    return request.app.state.langchain

async def get_chat_models(request: Request) -> dict:
    """
    Request 객체에서 app.state에 저장된 chat models를 추출하여 반환합니다.
    """
    return request.app.state.models


# ============================================================================
# Service Dependencies
# ============================================================================

from app.services.manual_service import ManualService
from app.repositories.manual import *

async def get_manual_service(
    # repository: ManualRepositoryProtocol = Depends(ManualEngineRepository),
    # repository: ManualRepositoryProtocol = Depends(ManualMockRepository),
    repository: ManualRepositoryProtocol = Depends(ManualSupabaseRepository),
)->ManualService:
    return ManualService(repository)


from app.services.healthz_service import HealthzService
from app.repositories.health import *
async def get_health_service(
    repository: HealthzRepositoryProtocol = Depends(HealthzSqlAlchemyRepository)
) -> HealthzService:
    return HealthzService(repository)