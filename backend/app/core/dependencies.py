from fastapi import Request
from supabase import AsyncClient

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