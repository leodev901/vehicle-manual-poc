import httpx
import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from app.base.logger import logger

T = TypeVar("T")

HTTP_RETRY_EXCEPTIONS = (
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.ConnectError,
    httpx.RemoteProtocolError,
)

class RetryExhaustedError(Exception):
    """정해진 재시도 횟수를 모두 사용해도 작업이 실패했을 때 발생합니다."""


async def retry_async(
    operation_name:str,
    operation: Callable[[], Awaitable[T]],
    *,
    max_attempts: int = 3,
    base_delay_seconds: float = 0.5,
    retry_exceptions: tuple[type[Exception], ...] = HTTP_RETRY_EXCEPTIONS    
)->T:
    """
    비동기 외부 호출에 재시도 정책을 적용합니다.

    operation_name:
        로그에 남길 작업 이름입니다. 예: "hf_embedding", "keyword_extraction"

    operation:
        실제로 실행할 비동기 함수입니다.
        인자를 받지 않는 lambda로 감싸서 넘기면 호출 시점을 retry_async가 제어할 수 있습니다.

    max_attempts:
        총 시도 횟수입니다. 3이면 최초 1회 + 재시도 2회를 의미합니다.

    base_delay_seconds:
        첫 재시도 전 대기 시간입니다.
        실패가 반복될수록 0.3s, 0.6s, 1.2s처럼 지수적으로 늘립니다.

    retry_exceptions:
        어떤 예외를 재시도할지 지정합니다.
        400/401 같은 재시도해도 소용없는 예외는 여기에 넣지 않는 것이 좋습니다.
    """

    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            return await operation()
        except retry_exceptions as exc:
            last_error = exc

            # 마지막 시도 이면 종료 
            if attempt == max_attempts:
                break

            logger.error(
                f"[retry] {operation_name} failed "
                f"attempt={attempt}/{max_attempts} "
                f"error={type(exc).__name__}; "
            )
            await asyncio.sleep(base_delay_seconds * attempt)
        ## 그 외 retry_exceptions에 포함되지 않은 Error 들은 except에 안 잡힘 → 즉시 함수 밖으로 전파

    raise RetryExhaustedError(
        f"{operation_name} failed after {max_attempts} attempts"
    ) from last_error


