import json
import uuid
import asyncio
from fastapi import Request
from fastapi.responses import StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.base.logger import logger

EXCLUDE_PATH = [
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/openapi.yaml",
]

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # OPTIONS 메소드는 skiip
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # health check, docs 등은 skip
        if request.url.path in EXCLUDE_PATH:
            return await call_next(request)

        trace_id = request.headers.get("trace-id") or str(uuid.uuid4())
        request.state.trace_id = trace_id

        logger.info(f"Request: [{trace_id}] {request.client.host if request.client else 'unknown'} | {request.method} | {request.url}")
        logger.info(f"Headers: [{trace_id}] {json.dumps(dict(request.headers), indent=2, ensure_ascii=False)}")

        response = await call_next(request)
        logger.info(f"Response: [{trace_id}] {response.status_code} ")
        return response

    
    