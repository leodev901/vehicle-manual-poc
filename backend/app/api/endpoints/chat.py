from fastapi import APIRouter, Depends, HTTPException, Request
from supabase import Client

from app.schemas.response import CommonResponse
from app.schemas.chat import ChatRequest
from app.core.dependencies import get_supabase_client, get_llm_client, get_langchain_client

from app.services.chat_service import ChatService

api_router = APIRouter(prefix="/api/v1", tags=["chat"])

@api_router.post("/chat", response_model=CommonResponse)
async def chat(
    payload: ChatRequest, 
    chat_Service: ChatService = Depends(ChatService),
):

    result = await chat_Service.chat(payload)
    return CommonResponse.ok(result)

@api_router.post("/chat/langchain", response_model=CommonResponse)
async def chat_langchain(
    payload: ChatRequest, 
    chat_Service: ChatService = Depends(ChatService),
):

    result = await chat_Service.chat_langchain(payload)
    return CommonResponse.ok(result)