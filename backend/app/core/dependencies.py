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

# ============================================================================
# Service Dependencies
# ============================================================================

from app.services.manual_service import ManualService
# app/repositories/manual/__init__.py를 임포트하면 이 파일의 네임스페이스로 함께 올라옵니다.
from app.repositories.manual import *

async def get_manual_service(
    # 상황에 따라 Database Repository 교체 가능 하도록 구성
    # repository: ManualRepositoryProtocol = Depends(ManualEngineRepository),
    # repository: ManualRepositoryProtocol = Depends(ManualMockRepository),
    repository: ManualRepositoryProtocol = Depends(ManualSupabaseRepository),
)->ManualService:
    return ManualService(repository)    