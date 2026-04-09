from fastapi import APIRouter, Depends, HTTPException, Request
from supabase import Client

from app.schemas.response import CommonResponse
from app.schemas.chat import ChatRequest
from app.core.dependencies import get_supabase_client, get_llm_client

from app.services.chat_service import ChatService

api_router = APIRouter(prefix="/api/v1", tags=["chat"])

@api_router.post("/chat", response_model=CommonResponse)
def chat(
    request: ChatRequest, 
    supabase: Client = Depends(get_supabase_client),
    llm: dict = Depends(get_llm_client),
    ):

    result = ChatService.chat(request, supabase, llm)
    return CommonResponse.ok(result)