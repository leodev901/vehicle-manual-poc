import time
from collections.abc import Awaitable, Callable
from enum import Enum
from typing import TypeVar

from app.base.logger import logger

T = TypeVar("T")


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(Exception):
    """Circuit이 OPEN 상태라 외부 호출을 차단할 때 발생합니다."""


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        *,
        failure_threshold: int = 5,
        recovery_timeout_seconds: float = 30.0,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.opened_at: float | None = None

    def _can_try_half_open(self) -> bool:
        if self.opened_at is None:
            return False

        return (time.monotonic() - self.opened_at) >= self.recovery_timeout_seconds

    async def call(self, operation: Callable[[], Awaitable[T]]) -> T:
        if self.state == CircuitState.OPEN:
            if not self._can_try_half_open():
                raise CircuitOpenError(f"{self.name} circuit is open")

            # 일정 시간이 지난 뒤 딱 한 번 시험 호출을 허용합니다.
            self.state = CircuitState.HALF_OPEN

        try:
            result = await operation()

        except Exception:
            self._record_failure()
            raise

        self._record_success()
        return result

    def _record_failure(self) -> None:
        self.failure_count += 1

        logger.error(
            f"[circuit] {self.name} failure_count="
            f"{self.failure_count}/{self.failure_threshold}"
        )

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.opened_at = time.monotonic()
            logger.error(f"[circuit] {self.name} opened")

    def _record_success(self) -> None:
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.opened_at = None
