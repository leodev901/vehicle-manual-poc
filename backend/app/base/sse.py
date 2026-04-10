# SSE Handler (Wrapper)
import json
import asyncio
from typing import AsyncIterable, AsyncGenerator
from fastapi.responses import StreamingResponse

from app.base.logger import logger

class SafeGuardStreamingResponse(StreamingResponse):
    def __init__(
        self, 
        content: AsyncIterable,
        *args, **kwargs
    ):
        self.trace_id = kwargs.pop("trace_id", "unknown")
        super().__init__(
            content=self._safe_wrapper(content),
            *args, **kwargs
        )
        
    async def _safe_wrapper(self, generator: AsyncIterable) -> AsyncGenerator:
        try:
            async for chunk in generator:
                yield chunk
                
        except asyncio.CancelledError:
            # [추가] 클라이언트 연결 끊김 정상 처리 (에러 로깅 방지)
            logger.info(f"[{self.trace_id}] Client disconnected during SSE stream.")
            raise  # 프레임워크가 자원을 정리할 수 있도록 위로 던짐        
        
        except Exception as e:
            # 서버 내부 로깅 (raw exception 기록)
            logger.error(f"[{self.trace_id}] SSE stream error: {type(e).__name__} - {e}")
            # 클라이언트에는 사용자 친화적 메시지만 전송
            yield f'data: {json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)}\n\n'
        

    

# wrpper 방식 대신에 StreamingResponse를 상속받아 사용
# async def sse_handler(
#     generator: AsyncGenerator,
#     trace_id: str,
# )->AsyncGenerator[str, None]:
#     """
#     모든 LLM 스트리밍 제네레이터를 감싸서 event: error로 변환 하는 전역 래퍼
#     HTTP 전역 핸들러가 하는 역할을 스트림 레이어에서 수행.
    
#     - 예외 발생 시 raw exception 노출 없이 SSE 에러 이벤트로 변환
#     - 서버 로그에는 전체 에러 기록
#     """
#     try:
#         async for chunk in generator:
#             yield chunk
#     except Exception as e:
#         # 서버 내부 로깅 (raw exception 기록)
#         logger.error(f"[{trace_id}] SSE stream error: {type(e).__name__} - {e}")
#         # 클라이언트에는 사용자 친화적 메시지만 전송
#         yield f'data: {json.dumps({"status": "error", "message": "요청 처리 중 오류가 발생했습니다."}, ensure_ascii=False)}\n\n'
        
        