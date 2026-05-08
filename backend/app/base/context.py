from contextvars import ContextVar, Token
from typing import Optional


_trace_id_ctx_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)


def get_trace_id() -> str:
    return _trace_id_ctx_var.get() if _trace_id_ctx_var.get() else "unknown"

def bind_trace_id(trace_id: str) -> Token[str]:
    """
    현재 async context에 trace_id를 바인딩합니다.
    반환된 token은 요청 종료 시 원래 값으로 복구할 때 사용합니다.
    """
    return _trace_id_ctx_var.set(trace_id)

def reset_trace_id(token: Token[str]) -> None:
    """
    bind_trace_id() 이전 상태로 trace_id 컨텍스트를 복구합니다.
    clear 방식보다 중첩 context에서 안전합니다.
    """
    _trace_id_ctx_var.reset(token)