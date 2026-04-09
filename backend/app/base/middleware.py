from fastapi import Request
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

        logger.info(f"Request: {request.client.host if request.client else 'unknown'} | {request.method} | {request.url} | {request.body}")
        try:
            response = await call_next(request)
            logger.info(f"Response: {response.status_code} ")
            return response
        except Exception as e:
            logger.error(f"{type(e).__name__} - {e}")
            raise e
        
    