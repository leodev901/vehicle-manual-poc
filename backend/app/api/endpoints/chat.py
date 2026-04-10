from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.schemas.response import CommonResponse
from app.schemas.chat import ChatRequest
from app.base.sse import SafeGuardStreamingResponse

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

@api_router.post("/chat/stream")
async def chat_stream(
    request: Request,
    payload: ChatRequest,
    chat_service: ChatService = Depends(ChatService),
):
    # StreamingResponse 객체에 서비스의 제너레이터 함수를 통째로 넣어야 스트리밍 됨.
    # streaMiddelaware에서 응답 갭체에 에러 바생시 에러 yield 하도록 구현 함
    return SafeGuardStreamingResponse(
        chat_service.chat_stream(payload),
        media_type="text/event-stream", # 브라우저에게 "이거 안 끝나는 실시간 이벤트야!" 명시해줌
        trace_id=getattr(request.state, "trace_id", "unknown")
    )
