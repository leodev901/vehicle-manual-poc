from http import HTTPStatus
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from postgrest.exceptions import APIError

from app.base.logger import logger


def register_exception_handlers(app: FastAPI):
    """FastAPI exception handler 등록
    """
    logger.info("Registering exception handlers...")
    app.add_exception_handler(Exception, global_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handelr)
    app.add_exception_handler(RequestValidationError, request_validation_error_handler)
    app.add_exception_handler(APIError, supabse_exception_handler)


# Supabse(PostgRest)에서 발생하는 모든 APIError를 가로채서 FastAPI규격에 맞는 JSON 응답으로 반환합니다.
async def supabse_exception_handler(request: Request, exc: APIError):
    """Supabse(PostgRest)에서 발생하는 모든 APIError를 가로채서 FastAPI규격에 맞는 JSON 응답으로 반환합니다.
    """
    error_dtails = exc.json() if hasattr(exc, "json") else str(exc)
    logger.error(f"[{getattr(request.state,'trace_id','unknown')}] {type(exc).__name__} - {error_dtails}")

    return JSONResponse(
        status_code=HTTPStatus.BAD_REQUEST,
        content={
            "success": False,
            "error": "Databse Error",
            "code": exc.code,
            "message": exc.message,
            "details": exc.details,
            "hint": exc.hint,
        }
    )
    
    

# HTTPException을 던지면 이 핸들러가 잡아서 JSONResponse로 변환해서 리턴
async def http_exception_handelr(request: Request, exc: HTTPException):
    """HTTPException을 던지면 이 핸들러가 잡아서 JSONResponse로 변환해서 리턴
    """

    logger.error(f"[{getattr(request.state,'trace_id','unknown')}] {type(exc).__name__} -{exc.status_code}- {exc}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error_code": exc.status_code,
            "message": exc.detail
        }
    )

# RequestValidationError
async def request_validation_error_handler(request: Request, exc: RequestValidationError):
    logger.error(f"[{getattr(request.state,'trace_id','unknown')}] {type(exc).__name__} - {exc}")
    return JSONResponse(
        status_code=HTTPStatus.BAD_REQUEST,
        content={
            "success": False,
            "error_code": HTTPStatus.BAD_REQUEST,
            "message": "입력값 또는 형식이 잘못되었습니다."
        }
    )

# global exception handler  - 최상위 Exception을 잡기 위한 핸들러
async def global_exception_handler(request: Request, exc: Exception):
    """global exception handler  - 최상위 Exception을 잡기 위한 핸들러
    """
    logger.error(f"[{getattr(request.state,'trace_id','unknown')}] {type(exc).__name__} - {exc}")
    # raise HTTPException(status_code=500, detail="Internal server error")
    return JSONResponse(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error_code": 500,
            "message": "요청 처리 중 오류가 발생했습니다."
        }
    )