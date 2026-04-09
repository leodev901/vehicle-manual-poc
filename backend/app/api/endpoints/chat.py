from fastapi import APIRouter, Depends, HTTPException, Request
from supabase import Client

from app.schemas.response import CommonResponse
from app.schemas.chat import ChatRequest
from app.core.dependencies import get_supabase_client

api_router = APIRouter(prefix="/api/v1", tags=["chat"])

@api_router.post("/chat", response_model=CommonResponse)
def chat(request: ChatRequest, supabase: Client = Depends(get_supabase_client)):
    
    return CommonResponse.ok({"message": "chat"})