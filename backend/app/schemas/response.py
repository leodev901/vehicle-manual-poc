from http import HTTPStatus
from typing import Generic, TypeVar

from pydantic import BaseModel

T =TypeVar("T")

class CommonResponse(BaseModel, Generic[T]):
    http_status_code: int = HTTPStatus.OK
    message: str = "요청이 완료되었습니다."
    data: T | None = None

    # =====================
    # 성공 결과 리턴
    # =====================
    
    
    @staticmethod
    def ok(data) -> "CommonResponse":
        return CommonResponse(data=data)
    
    @staticmethod
    def created(data) :
        return CommonResponse(http_status_code=HTTPStatus.CREATED, data=data)
    
    @staticmethod
    def no_content() -> "CommonResponse":
        return CommonResponse(http_status_code=HTTPStatus.NO_CONTENT)
    

    # =====================
    # 오류 메세지 리턴
    # =====================
    
    @staticmethod
    def bad_request(message: str = "잘못된 요청입니다.") -> "CommonResponse":
        return CommonResponse(http_status_code=HTTPStatus.BAD_REQUEST, message=message)

    @staticmethod
    def not_found(message: str = "요청한 자원을 찾을 수 없습니다.") -> "CommonResponse":
        return CommonResponse(http_status_code=HTTPStatus.NOT_FOUND, message=message)

    @staticmethod
    def unauthorized(message: str = "인증되지 않은 사용자입니다.") -> "CommonResponse":
        return CommonResponse(http_status_code=HTTPStatus.UNAUTHORIZED, message=message)
      
    @staticmethod
    def error( message: str = "요청 처리 중 오류가 발생했습니다.") -> "CommonResponse":
        return CommonResponse(http_status_code=HTTPStatus.INTERNAL_SERVER_ERROR, message=message)

    @staticmethod
    def forbidden(message: str = "접근 권한이 없습니다.") -> "CommonResponse":
        return CommonResponse(http_status_code=HTTPStatus.FORBIDDEN, message=message)
    
