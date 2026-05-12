# 4-2 학습 노트: 외부 API 방어막과 시맨틱 캐싱

## 1. 이번 단계의 목표

4-1에서는 DB 커넥션 풀이 Pod/Worker 증가에 따라 어떻게 커지는지 확인했습니다.
4-2에서는 RAG 챗봇이 의존하는 외부 API가 느려지거나 실패할 때, 백엔드가 같이 무너지지 않도록 방어막을 설계합니다.

대상 엔드포인트는 다음입니다.

```http
POST /api/v1/chat/stream/advanced
```

현재 핵심 구현은 `backend/app/services/chat_service.py`의 `chat_stream_advanced()`입니다.

### 현재 구현 체크포인트

2026-05-12 기준으로 4-2는 아래 상태입니다.

| 항목 | 상태 | 구현/위치 |
|---|---|---|
| SSE 에러 가드 | 진행 중 | `backend/app/base/sse.py`에서 스트리밍 예외를 `event: error`로 변환 |
| Retry 유틸리티 | 진행 완료 | `backend/app/utils/retry.py`의 `retry_async()` |
| Hugging Face 임베딩 client 분리 | 진행 완료 | `backend/app/base/embedding_client.py` |
| In-memory 임베딩 캐시 | 진행 완료 | `backend/app/utils/in_memory_cache.py` |
| `chat_stream_advanced()` 연결 | 진행 완료 | 키워드 추출 retry, 임베딩 retry, 임베딩 벡터 cache get/set 적용 |
| Circuit Breaker | 미완료 | 반복 장애 차단 정책 필요 |
| Provider Fallback | 미완료 | OpenAI/Gemini/Grok 우회 정책 필요 |
| Redis 분산 캐시 | 보류 | 현재는 단일 프로세스 학습용 in-memory cache 사용 |

> 현재 in-memory cache는 학습용입니다. 서버 재시작, 다중 worker, 다중 pod 환경에서는 캐시가 공유되지 않습니다.

---

## 2. 현재 `chat_stream_advanced()` 흐름

현재 요청은 아래 순서로 흐릅니다.

```text
Client
  ↓
FastAPI Router
  ↓
SafeGuardStreamingResponse
  ↓
ChatService.chat_stream_advanced()
  ↓
1. LLM 모델 선택
  ↓
2. LLM 키워드 추출
  ↓
3. Hugging Face 임베딩 서버 호출
  ↓
4. Supabase RPC hybrid_search 호출
  ↓
5. LLM 최종 답변 스트리밍
  ↓
SSE chunk 응답
```

ASCII로 조금 더 자세히 보면 이렇습니다.

```text
┌────────────┐
│  Browser   │
└─────┬──────┘
      │ POST /api/v1/chat/stream/advanced
      ▼
┌───────────────────────────────┐
│ SafeGuardStreamingResponse     │
│ - generator 예외 감싸기        │
│ - SSE error message 반환       │
└─────┬─────────────────────────┘
      ▼
┌───────────────────────────────┐
│ chat_stream_advanced()         │
└─────┬─────────────────────────┘
      │
      ├─ 1) provider/model 선택
      │
      ├─ 2) keyword extraction
      │      └─ OpenAI / Gemini / Grok
      │
      ├─ 3) embedding
      │      └─ Hugging Face Inference Server
      │
      ├─ 4) RAG search
      │      └─ Supabase RPC hybrid_search
      │
      └─ 5) answer streaming
             └─ OpenAI / Gemini / Grok
```

여기서 장애가 날 수 있는 외부 의존성은 4개입니다.

| 단계 | 외부 의존성 | 현재 코드 위치 | 대표 장애 |
|---|---|---|---|
| 키워드 추출 | LLM provider | `model.ainvoke(...)` | timeout, rate limit, 5xx |
| 임베딩 생성 | Hugging Face Inference Server | `client.post(settings.HF_INFERENCE_URL, ...)` | cold start, timeout, 5xx |
| RAG 검색 | Supabase RPC | `repo.search_manual_rag(...)` | DB 부하, RPC 실패, 연결 지연 |
| 최종 답변 | LLM provider | `rag_chain.astream(...)` | stream 중단, timeout, rate limit |

---

## 3. 방어막 설계 원칙

외부 API 방어는 무조건 retry를 많이 넣는 것이 아닙니다.
실패의 종류에 따라 다르게 대응해야 합니다.

| 장애 유형 | 예시 | 대응 |
|---|---|---|
| 일시적 네트워크 오류 | DNS, connect timeout, read timeout | 짧은 retry 가능 |
| 외부 서버 과부하 | 502, 503, 504 | backoff retry 가능 |
| 요청 자체 문제 | 400, 401, 403 | retry 금지 |
| rate limit | 429 | `Retry-After` 또는 긴 backoff |
| 스트리밍 중 실패 | 답변 생성 중 연결 끊김 | 무분별한 retry 금지, 사용자 안내 |
| 반복 장애 | 같은 API가 계속 실패 | circuit breaker open |

핵심 기준은 다음입니다.

```text
Retry는 "잠깐 다시 하면 성공할 가능성이 있는 실패"에만 사용한다.
Circuit Breaker는 "계속 실패 중인 외부 시스템을 잠시 호출하지 않는 장치"다.
Cache는 "외부 호출 자체를 줄이는 비용/지연 최적화 장치"다.
```

---

## 4. 어디에 Timeout을 둘까?

Timeout은 가장 먼저 필요합니다.
Timeout이 없으면 외부 API 장애가 생겼을 때 coroutine이 오래 붙잡혀 서버 자원을 잠식합니다.

현재 `backend/app/base/http_client.py`에는 Hugging Face 임베딩 호출에 쓰는 공통 `httpx.AsyncClient` timeout이 있습니다.

```python
timeout=Timeout(
    timeout=60.0,
    connect=10.0,
    read=10.0,
    write=10.0,
    pool=5.0,
)
```

이 설정은 임베딩 서버 HTTP 호출에는 적용됩니다.
하지만 LLM `ainvoke()`와 `astream()` 단계는 provider SDK / LangChain 모델 설정 영역이므로, 별도 timeout 정책이 필요합니다.

```text
Timeout 적용 위치

1. Keyword LLM 호출
   - 목표: 키워드 추출이 오래 걸리면 빠르게 실패 처리

2. Hugging Face Embedding HTTP 호출
   - 현재 httpx timeout 적용됨
   - 필요 시 임베딩 전용 timeout으로 더 짧게 조정 가능

3. Supabase RPC
   - DB/RPC 호출 대기 시간이 길어질 때 방어

4. Final LLM Streaming
   - streaming은 중간 chunk가 계속 올 수 있으므로 일반 timeout과 다르게 설계
```

---

## 5. 어디에 Retry를 둘까?

Retry는 단계별로 다르게 적용해야 합니다.

```text
추천 retry 위치

Keyword LLM 호출:
  - 1~2회 retry 가능
  - 짧은 텍스트 생성이라 재시도 비용이 상대적으로 작음

Embedding HTTP 호출:
  - 2~3회 retry 가능
  - Hugging Face Spaces cold start / 503에 효과적

Supabase RPC:
  - 신중하게 1회 정도만
  - DB가 실제로 바쁜 상황에서 retry를 많이 하면 부하를 더 키움

Final LLM Streaming:
  - stream 시작 전 실패는 fallback/retry 가능
  - stream 중간 실패는 같은 답변을 이어붙이기 어려우므로 retry 지양
```

왜 최종 스트리밍은 retry를 조심해야 할까요?

```text
사용자가 이미 일부 토큰을 받음
    ↓
중간에 stream 실패
    ↓
서버가 retry해서 새 답변을 다시 생성
    ↓
앞에서 받은 문장과 새 답변이 충돌하거나 중복될 수 있음
```

그래서 스트리밍 중 장애는 "다시 생성"보다 "사용자에게 안전하게 안내하고 종료"가 더 낫습니다.

---

## 6. Circuit Breaker는 어디에 둘까?

Circuit Breaker는 반복 실패하는 외부 API를 잠시 차단합니다.

```text
정상 상태: CLOSED
  ↓ 실패 누적
차단 상태: OPEN
  ↓ 일정 시간 후
시험 상태: HALF_OPEN
  ↓ 성공하면
정상 복귀: CLOSED
```

ASCII로 보면 다음과 같습니다.

```text
             실패 횟수 임계치 초과
        ┌──────────────────────────┐
        │                          ▼
┌────────────┐              ┌────────────┐
│  CLOSED    │              │    OPEN    │
│ 정상 호출  │              │ 호출 차단  │
└─────┬──────┘              └─────┬──────┘
      ▲                           │
      │ 성공                      │ cooldown 경과
      │                           ▼
┌─────┴──────┐              ┌────────────┐
│  CLOSED    │◀─────────────│ HALF_OPEN  │
│ 정상 복귀  │   시험 성공  │ 시험 호출  │
└────────────┘              └────────────┘
```

적용 후보는 다음입니다.

| 대상 | Circuit Breaker 필요도 | 이유 |
|---|---:|---|
| Hugging Face 임베딩 서버 | 높음 | cold start, 무료 인프라, 5xx/timeout 가능성 |
| LLM provider | 높음 | rate limit, provider 장애, 비용 보호 |
| Supabase RPC | 중간 | DB 장애 시 retry보다 빠른 실패가 서버 보호에 유리 |

Circuit Breaker가 없으면 장애 상황에서 모든 요청이 계속 외부 API를 호출합니다.

```text
외부 API 장애
  ↓
모든 요청이 계속 호출
  ↓
timeout까지 대기
  ↓
서버 coroutine / connection pool 점유
  ↓
정상 요청까지 느려짐
```

Circuit Breaker가 있으면 일정 기간 빠르게 실패합니다.

```text
외부 API 장애 감지
  ↓
circuit OPEN
  ↓
잠시 외부 호출 차단
  ↓
사용자에게 "일시적으로 응답 생성이 어렵습니다" 안내
  ↓
서버 자원 보호
```

---

## 7. Provider Fallback은 어디에 둘까?

현재 프로젝트는 `openai`, `gemini`, `grok` 모델 registry를 가지고 있습니다.
따라서 특정 provider가 실패할 때 다른 provider로 우회할 수 있는 기반은 있습니다.

```text
요청 provider = openai
  ↓
OpenAI 실패
  ↓
fallback 후보 확인
  ↓
Gemini 또는 Grok으로 키워드 추출/답변 생성
```

다만 fallback에는 주의점이 있습니다.

| 주의점 | 이유 |
|---|---|
| 모델마다 답변 품질이 다름 | 같은 prompt라도 결과가 달라질 수 있음 |
| 비용 정책이 다름 | 비싼 모델로 fallback하면 비용 폭증 가능 |
| 스트리밍 중 fallback은 어렵다 | 이미 일부 답변이 사용자에게 전달됨 |
| 사용자 선택 모델을 무시할 수 있음 | 사용자가 명시적으로 provider를 골랐을 수 있음 |

그래서 추천 정책은 다음입니다.

```text
키워드 추출 단계:
  fallback 가능

최종 답변 생성 시작 전:
  fallback 가능

최종 답변 stream 중:
  fallback 지양
```

---

## 8. Cache는 어디에 둘까?

캐시는 "실패 후 복구"가 아니라 "외부 호출 자체를 줄이는 장치"입니다.

현재 흐름에서 캐시 후보는 세 가지입니다.

| 캐시 대상 | Key 후보 | Value | 효과 |
|---|---|---|---|
| 키워드 추출 결과 | normalized question | keywords | LLM 호출 절감 |
| 임베딩 결과 | keywords | query_vector | HF 호출 절감 |
| RAG 검색 결과 | model_id + keywords | top-k docs | Supabase RPC 절감 |
| 최종 답변 | model_id + provider + question | answer | LLM 비용 절감 |

다만 최종 답변 캐시는 조심해야 합니다.
차량 모델, provider, prompt 버전, 검색 결과가 바뀌면 같은 질문이라도 답이 달라질 수 있기 때문입니다.

추천 순서는 다음입니다.

```text
1단계: 임베딩 캐시
  - keywords가 같으면 vector도 거의 항상 같음
  - 비용/속도 개선 효과가 크고 위험이 낮음

2단계: RAG 검색 결과 캐시
  - model_id + keywords 기준
  - 매뉴얼 DB가 자주 바뀌지 않으면 효과적

3단계: 최종 답변 캐시
  - prompt_version, model_id, provider, question을 key에 포함해야 안전
```

Redis 캐시 구조 예시는 다음과 같습니다.

```text
cache:embedding:{hash(keywords)}
  -> [0.012, -0.153, ...]

cache:rag:{model_id}:{hash(keywords)}
  -> [{"heading": "...", "content": "...", "page_num": 12}, ...]

cache:answer:{model_id}:{provider}:{prompt_version}:{hash(question)}
  -> "매뉴얼 기준 답변 ..."
```

---

## 9. `chat_stream_advanced()` 기준 적용 지도

현재 함수에 방어막을 추가한다면 위치는 아래처럼 나눌 수 있습니다.

```text
async def chat_stream_advanced(payload):
    yield "AI 모델 로딩 중"

    # A. request validation / provider validation
    # - provider 없음, model 없음, model_id 없음 등 빠른 실패

    # B. keyword extraction
    # - timeout
    # - retry
    # - provider fallback 가능
    # - keyword cache 가능

    # C. embedding
    # - httpx timeout 이미 있음
    # - retry
    # - circuit breaker
    # - embedding cache 추천

    # D. Supabase RAG search
    # - 짧은 retry 또는 retry 없음
    # - circuit breaker 신중 적용
    # - RAG result cache 가능

    # E. answer generation streaming
    # - stream 시작 전 fallback 가능
    # - stream 중 retry 지양
    # - 사용자 친화적 SSE error 처리

    yield "[DONE]"
```

구조적으로는 `chat_stream_advanced()` 안에 모든 방어 로직을 직접 넣기보다, 역할별로 나누는 것이 좋습니다.

```text
ChatService
  ├─ KeywordExtractor
  ├─ EmbeddingClient
  ├─ ManualSearchService
  ├─ AnswerGenerator
  ├─ CircuitBreaker
  └─ CacheRepository
```

왜 나누는가?

```text
chat_stream_advanced()는 SSE 흐름을 조립하는 역할만 담당
각 외부 API 호출의 timeout/retry/cache는 별도 컴포넌트가 담당
테스트가 쉬워지고, 장애 정책을 바꾸기 쉬워짐
```

---

## 10. 구현 우선순위 제안

실제 코드 적용은 아래 순서가 안전합니다.

| 순서 | 작업 | 이유 |
|---:|---|---|
| 1 | SSE 에러 메시지 정리 | raw exception 노출 방지 |
| 2 | 외부 호출별 timeout 정책 명시 | 장애 시 무한 대기 방지 |
| 3 | HF 임베딩 호출 retry | cold start/일시 장애 대응 효과 큼 |
| 4 | HF 임베딩 circuit breaker | 무료/외부 인프라 장애 전파 차단 |
| 5 | Redis embedding cache | 비용과 latency 개선, 위험 낮음 |
| 6 | LLM provider fallback | 모델 품질/비용 정책까지 함께 고려 필요 |
| 7 | 최종 답변 semantic cache | key 설계와 prompt version 관리 필요 |

---

## 11. 4-2 완료 기준

아래를 설명하고 설계할 수 있으면 4-2 이론 단계는 완료입니다.

- [x] 외부 API 장애 유형별로 retry 가능/불가능을 구분할 수 있다.
- [x] Timeout, Retry, Circuit Breaker의 역할 차이를 설명할 수 있다.
- [x] `chat_stream_advanced()` 흐름에서 각 방어막을 어디에 둘지 설명할 수 있다.
- [x] 스트리밍 중 retry가 위험한 이유를 설명할 수 있다.
- [ ] Redis 캐시 key에 `model_id`, `provider`, `prompt_version`이 필요한 이유를 설명할 수 있다.
- [ ] raw exception을 사용자에게 직접 노출하지 않는 SSE 에러 응답 정책을 구현 수준에서 마무리한다.
- [ ] Circuit Breaker를 실제 코드에 적용하고 장애 상황에서 빠른 실패를 검증한다.

---

## 12. 구현 예시 1: SSE 에러 메시지 표준화

현재 `SafeGuardStreamingResponse`는 내부 예외 메시지 `str(e)`를 사용자에게 그대로 내려줄 수 있습니다.
운영 환경에서는 raw exception을 사용자에게 보여주면 안 됩니다.

아래 예시는 서버 로그에는 자세한 원인을 남기고, 사용자에게는 안전한 메시지만 내려보내는 방식입니다.

> 주의: 아래 코드는 학습용 예시입니다. 실제 코드에 적용할 때는 프로젝트 정책에 맞게 diff로 반영합니다.

```python
# backend/app/base/sse.py

import json
import asyncio
from typing import AsyncIterable, AsyncGenerator
from fastapi.responses import StreamingResponse

from app.base.logger import logger


class SafeGuardStreamingResponse(StreamingResponse):
    def __init__(
        self,
        content: AsyncIterable,
        *args,
        **kwargs,
    ):
        self.trace_id = kwargs.pop("trace_id", "unknown")
        super().__init__(
            content=self._safe_wrapper(content),
            *args,
            **kwargs,
        )

    async def _safe_wrapper(self, generator: AsyncIterable) -> AsyncGenerator[str, None]:
        try:
            async for chunk in generator:
                yield chunk

        except asyncio.CancelledError:
            # 클라이언트가 브라우저 탭을 닫거나 네트워크가 끊긴 상황입니다.
            # 서버 장애가 아니므로 error 로그가 아니라 info 로그로 남깁니다.
            logger.info(f"[{self.trace_id}] Client disconnected during SSE stream.")
            raise

        except Exception as exc:
            # 내부 로그에는 예외 타입과 내용을 남깁니다.
            # 운영 장애 분석에는 실제 원인이 필요하기 때문입니다.
            logger.error(
                f"[{self.trace_id}] SSE stream error: {type(exc).__name__} - {exc}"
            )

            # 사용자에게는 내부 예외 내용을 숨기고, 복구 가능한 안내 문구만 보냅니다.
            # event: error를 명시하면 프론트엔드가 일반 token과 에러를 쉽게 구분할 수 있습니다.
            safe_payload = {
                "status": "error",
                "message": "요청 처리 중 일시적인 문제가 발생했습니다. 잠시 후 다시 시도해 주세요.",
            }
            yield "event: error\n"
            yield f"data: {json.dumps(safe_payload, ensure_ascii=False)}\n\n"
```

왜 이렇게 하는가?

| 처리 | 이유 |
|---|---|
| `logger.error(...)` | 운영자는 실제 장애 원인을 알아야 함 |
| 사용자 메시지 고정 | DB host, API token, stack trace 같은 내부 정보 노출 방지 |
| `event: error` 사용 | 프론트에서 일반 token과 error를 명확히 분리 |

---

## 13. 구현 예시 2: Retry 유틸리티

Retry는 여러 외부 호출에서 반복해서 필요합니다.
매번 `for`문을 직접 쓰면 정책이 흩어지므로 공통 함수로 빼는 편이 좋습니다.

아래 예시는 별도 라이브러리 없이 구현한 단순 retry입니다.
로드맵에 적힌 `Tenacity`를 쓰면 더 풍부한 정책을 선언적으로 만들 수 있지만, 먼저 원리를 이해하기에는 직접 구현이 좋습니다.

```python
# backend/app/base/resilience.py

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from app.base.logger import logger

T = TypeVar("T")


class RetryExhaustedError(Exception):
    """정해진 재시도 횟수를 모두 사용해도 작업이 실패했을 때 던지는 예외입니다."""


async def retry_async(
    operation_name: str,
    operation: Callable[[], Awaitable[T]],
    *,
    max_attempts: int = 3,
    base_delay_seconds: float = 0.3,
    retry_exceptions: tuple[type[Exception], ...] = (Exception,),
) -> T:
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

            # 마지막 시도까지 실패했다면 더 기다리지 않고 종료합니다.
            if attempt == max_attempts:
                break

            delay = base_delay_seconds * (2 ** (attempt - 1))
            logger.error(
                f"[retry] {operation_name} failed "
                f"attempt={attempt}/{max_attempts} "
                f"error={type(exc).__name__}; retry_after={delay:.2f}s"
            )
            await asyncio.sleep(delay)

    raise RetryExhaustedError(
        f"{operation_name} failed after {max_attempts} attempts"
    ) from last_error
```

사용 예시는 다음과 같습니다.

```python
# Hugging Face 임베딩 호출에 retry 적용 예시

import httpx

query_vector = await retry_async(
    "hf_embedding",
    lambda: embedding_client.embed(keywords),
    max_attempts=3,
    base_delay_seconds=0.5,
    retry_exceptions=(
        httpx.ConnectTimeout,
        httpx.ReadTimeout,
        httpx.ConnectError,
        httpx.RemoteProtocolError,
    ),
)
```

왜 HTTP 401, 403, 400은 retry하지 않을까?

```text
401 Unauthorized → 토큰이 틀림. 다시 해도 실패.
403 Forbidden    → 권한이 없음. 다시 해도 실패.
400 Bad Request  → 요청 형식이 틀림. 다시 해도 실패.
```

Retry는 "시간이 지나면 성공할 수 있는 장애"에만 걸어야 합니다.

---

## 14. 구현 예시 3: Circuit Breaker

Circuit Breaker는 외부 API가 계속 실패할 때, 일정 시간 동안 호출 자체를 막습니다.
이렇게 하면 장애 난 외부 시스템을 계속 두드리느라 서버 자원을 낭비하지 않습니다.

```python
# backend/app/base/resilience.py

import time
from enum import Enum
from collections.abc import Awaitable, Callable
from typing import TypeVar

from app.base.logger import logger

T = TypeVar("T")


class CircuitState(str, Enum):
    CLOSED = "closed"      # 정상 호출 가능
    OPEN = "open"          # 호출 차단
    HALF_OPEN = "half_open"  # 복구 여부 시험 호출 1회 허용


class CircuitOpenError(Exception):
    """Circuit이 OPEN 상태라 외부 호출을 차단할 때 사용하는 예외입니다."""


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
        # OPEN 상태가 된 뒤 일정 시간이 지났는지 확인합니다.
        # 시간이 지났다면 외부 API가 회복됐는지 시험 호출을 허용합니다.
        if self.opened_at is None:
            return False
        return (time.monotonic() - self.opened_at) >= self.recovery_timeout_seconds

    async def call(self, operation: Callable[[], Awaitable[T]]) -> T:
        if self.state == CircuitState.OPEN:
            if not self._can_try_half_open():
                raise CircuitOpenError(f"{self.name} circuit is open")

            # cooldown 시간이 지난 뒤에는 딱 한 번 시험 호출을 허용합니다.
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
        # 성공하면 circuit을 정상 상태로 되돌립니다.
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.opened_at = None
```

사용 예시는 다음과 같습니다.

```python
# 앱 시작 시 또는 서비스 생성 시 provider별 breaker를 만들어 둡니다.
hf_embedding_breaker = CircuitBreaker(
    name="hf_embedding",
    failure_threshold=5,
    recovery_timeout_seconds=30.0,
)


# 임베딩 호출 시 breaker로 감쌉니다.
query_vector = await hf_embedding_breaker.call(
    lambda: retry_async(
        "hf_embedding",
        lambda: embedding_client.embed(keywords),
        max_attempts=3,
        base_delay_seconds=0.5,
    )
)
```

Circuit Breaker와 Retry를 같이 쓸 때는 보통 이렇게 생각합니다.

```text
Retry:
  요청 1건 안에서 잠깐 다시 시도

Circuit Breaker:
  여러 요청에 걸쳐 외부 API가 계속 실패하는지 감시
```

---

## 15. 구현 예시 4: Hugging Face EmbeddingClient 분리

현재 `chat_stream_advanced()` 안에는 임베딩 HTTP 호출 코드가 직접 들어 있습니다.
이 코드를 별도 클라이언트로 분리하면 timeout, retry, circuit breaker, cache를 붙이기 쉬워집니다.

```python
# backend/app/clients/embedding_client.py

import httpx

from app.base.http_client import get_httpx_client
from app.core.config import settings
from app.base.logger import logger


class EmbeddingClientError(Exception):
    """임베딩 서버 호출 실패를 서비스 계층에서 구분하기 위한 예외입니다."""


class EmbeddingClient:
    async def embed(self, text: str) -> list[float]:
        """
        Hugging Face 임베딩 서버에 텍스트를 보내고 벡터를 반환합니다.

        이 클래스가 하는 일:
        - HTTP 호출 세부사항을 ChatService에서 분리
        - 응답 형식 검증
        - 사용자에게 노출하지 않을 내부 예외를 도메인 예외로 변환
        """
        client = await get_httpx_client()

        try:
            response = await client.post(
                settings.HF_INFERENCE_URL,
                headers={
                    "Authorization": f"Bearer {settings.HF_TOKEN}",
                },
                json={
                    # 임베딩 서버는 text 필드를 입력으로 받습니다.
                    "text": text,
                },
            )
            response.raise_for_status()

        except httpx.HTTPStatusError as exc:
            # 4xx/5xx 응답은 여기로 들어옵니다.
            # 로그에는 상태 코드를 남겨야 장애 원인을 구분할 수 있습니다.
            logger.error(
                f"Embedding server returned error status={exc.response.status_code}"
            )
            raise EmbeddingClientError("임베딩 서버 응답이 올바르지 않습니다.") from exc

        except httpx.HTTPError as exc:
            # timeout, connect error 등 네트워크 계열 오류입니다.
            logger.error(f"Embedding server request failed: {type(exc).__name__}")
            raise EmbeddingClientError("임베딩 서버에 연결할 수 없습니다.") from exc

        payload = response.json()
        embedding = payload.get("embedding")

        if not embedding:
            # 응답은 200이지만 body가 기대한 형식이 아닌 경우입니다.
            logger.error("Embedding server response has no embedding field")
            raise EmbeddingClientError("임베딩 벡터를 생성하지 못했습니다.")

        return embedding
```

이렇게 분리하면 `ChatService`는 HTTP 세부사항을 몰라도 됩니다.

```python
query_vector = await embedding_client.embed(keywords)
```

---

## 16. 구현 예시 5: Redis CacheRepository

Redis를 붙이면 동일한 키워드에 대한 임베딩 호출을 줄일 수 있습니다.
처음에는 최종 답변 전체를 캐시하기보다 임베딩 벡터부터 캐시하는 것이 안전합니다.

```python
# backend/app/repositories/cache/redis_repository.py

import hashlib
import json
from typing import Any


class RedisCacheRepository:
    def __init__(self, redis_client):
        self.redis = redis_client

    def _hash(self, value: str) -> str:
        # Redis key에 긴 자연어를 그대로 넣으면 관리가 어렵습니다.
        # SHA-256으로 고정 길이 key를 만들면 안전하고 일관됩니다.
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def embedding_key(self, keywords: str) -> str:
        # 키 이름에 용도를 넣으면 Redis에서 디버깅하기 쉽습니다.
        return f"cache:embedding:{self._hash(keywords)}"

    async def get_json(self, key: str) -> Any | None:
        raw = await self.redis.get(key)
        if raw is None:
            return None

        # redis-py 설정에 따라 bytes로 올 수 있으므로 문자열로 변환합니다.
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")

        return json.loads(raw)

    async def set_json(self, key: str, value: Any, *, ttl_seconds: int) -> None:
        # TTL을 반드시 둡니다.
        # 캐시는 원본 데이터가 아니므로 영구 저장하면 오래된 답변/벡터가 남을 수 있습니다.
        raw = json.dumps(value, ensure_ascii=False)
        await self.redis.set(key, raw, ex=ttl_seconds)
```

임베딩 캐시 사용 예시는 다음과 같습니다.

```python
cache_key = cache_repository.embedding_key(keywords)
cached_vector = await cache_repository.get_json(cache_key)

if cached_vector is not None:
    # 캐시 hit이면 Hugging Face 서버를 호출하지 않습니다.
    query_vector = cached_vector
else:
    # 캐시 miss일 때만 외부 임베딩 서버를 호출합니다.
    query_vector = await embedding_client.embed(keywords)

    # 임베딩 결과는 일정 시간 동안 재사용합니다.
    await cache_repository.set_json(
        cache_key,
        query_vector,
        ttl_seconds=60 * 60 * 24,
    )
```

---

## 17. 구현 예시 6: Provider Fallback

Provider fallback은 실패한 모델 대신 다른 모델을 시도하는 전략입니다.
다만 사용자가 명시적으로 provider를 고른 경우에는 UX 정책이 필요합니다.

아래 예시는 "키워드 추출 단계"에 fallback을 적용하는 방식입니다.

```python
# backend/app/services/llm_fallback.py

from langchain_core.prompts import PromptTemplate

from app.base.logger import logger


class LlmFallbackError(Exception):
    """모든 provider가 실패했을 때 사용하는 예외입니다."""


async def invoke_with_provider_fallback(
    *,
    models: dict,
    preferred_provider: str,
    fallback_providers: list[str],
    model_name: str,
    prompt: PromptTemplate,
    prompt_variables: dict,
) -> str:
    """
    preferred_provider부터 호출하고, 실패하면 fallback provider를 순서대로 시도합니다.

    주의:
    - 최종 답변 스트리밍 중 fallback은 권장하지 않습니다.
    - 이 예시는 짧은 단건 호출인 키워드 추출에 적합합니다.
    """
    providers = [preferred_provider, *fallback_providers]
    last_error: Exception | None = None

    for provider in providers:
        if provider not in models:
            continue

        try:
            model = models[provider].with_config(
                configurable={"model": model_name}
            )
            response = await model.ainvoke(prompt.format(**prompt_variables))
            return response.content.strip()

        except Exception as exc:
            last_error = exc
            logger.error(
                f"LLM provider failed provider={provider} "
                f"error={type(exc).__name__}"
            )

    raise LlmFallbackError("사용 가능한 LLM provider가 없습니다.") from last_error
```

사용 예시는 다음과 같습니다.

```python
keywords = await invoke_with_provider_fallback(
    models=self.models,
    preferred_provider=provider,
    fallback_providers=["gemini", "grok", "openai"],
    model_name=payload.llm_config.model,
    prompt=MANUAL_KEYWORD_EXTRACTION_PROMPT,
    prompt_variables={"question": payload.message},
)
```

실무에서는 fallback provider마다 기본 모델명이 다를 수 있으므로 아래처럼 매핑을 두는 편이 더 안전합니다.

```python
fallback_model_map = {
    "openai": "gpt-5-nano",
    "gemini": "gemini-2.5-flash-lite",
    "grok": "grok-beta",
}
```

---

## 18. 구현 예시 7: 방어막이 적용된 `chat_stream_advanced()` 흐름

아래는 모든 개념을 합친 의사 코드입니다.
실제 적용 시에는 한 번에 다 넣지 말고, 우선순위대로 작은 PR/커밋으로 나누는 것이 좋습니다.

```python
async def chat_stream_advanced(self, payload: ChatRequest):
    yield 'data: {"status": "processing", "message": "AI 모델을 준비 중입니다..."}\n\n'

    provider = (payload.llm_config.provider or "grok").lower()
    if provider not in self.models:
        # 내부 로그에는 자세히 남기고, 사용자 메시지는 SafeGuardStreamingResponse가 처리합니다.
        logger.error(f"Unsupported LLM provider: {provider}")
        raise ValueError("지원하지 않는 LLM 제공자입니다.")

    # 1. 키워드 추출
    # - 짧은 LLM 호출이므로 timeout/retry/fallback을 적용하기 좋습니다.
    # - 같은 질문이 반복된다면 keyword cache도 가능합니다.
    keywords = await retry_async(
        "keyword_extraction",
        lambda: extract_keywords_with_timeout_and_fallback(payload),
        max_attempts=2,
        base_delay_seconds=0.3,
    )

    yield 'data: {"status": "processing", "message": "관련 문서를 검색 중입니다..."}\n\n'

    # 2. 임베딩 캐시 확인
    # - 캐시 hit이면 외부 HF 서버를 호출하지 않습니다.
    embedding_cache_key = cache_repository.embedding_key(keywords)
    query_vector = await cache_repository.get_json(embedding_cache_key)

    if query_vector is None:
        # 3. 임베딩 서버 호출
        # - retry는 요청 1건 안의 일시 장애 대응입니다.
        # - circuit breaker는 여러 요청에 걸친 반복 장애 차단입니다.
        query_vector = await hf_embedding_breaker.call(
            lambda: retry_async(
                "hf_embedding",
                lambda: embedding_client.embed(keywords),
                max_attempts=3,
                base_delay_seconds=0.5,
            )
        )

        await cache_repository.set_json(
            embedding_cache_key,
            query_vector,
            ttl_seconds=60 * 60 * 24,
        )

    # 4. RAG 검색
    # - DB가 이미 바쁜 상황에서 retry를 많이 하면 장애를 키울 수 있습니다.
    # - 그래서 짧은 retry 또는 retry 없음이 안전합니다.
    results = await manual_search_service.search(
        model_id=payload.model_id,
        query=keywords,
        query_vector=query_vector,
        top_k=4,
    )

    context = format_manual_context(results)

    yield 'data: {"status": "generating", "message": "답변을 생성 중입니다..."}\n\n'

    # 5. 최종 답변 스트리밍
    # - stream 중간 retry는 문장 중복/충돌 위험이 있어 지양합니다.
    # - 에러가 나면 SafeGuardStreamingResponse가 안전한 SSE error로 변환합니다.
    async for chunk in answer_generator.stream(
        provider=provider,
        model_name=payload.llm_config.model,
        context=context,
        question=payload.message,
    ):
        yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

    yield "data: [DONE]\n\n"
```

위 예시에서 함수가 나뉜 이유는 SRP 때문입니다.

| 컴포넌트 | 책임 |
|---|---|
| `ChatService` | SSE 흐름 조립 |
| `EmbeddingClient` | HF 임베딩 HTTP 호출 |
| `CircuitBreaker` | 반복 장애 차단 |
| `retry_async` | 일시 장애 재시도 |
| `CacheRepository` | Redis 캐시 입출력 |
| `ManualSearchService` | RAG 검색 |
| `AnswerGenerator` | 최종 LLM 답변 생성 |

이 구조로 나누면 장애 정책을 바꾸더라도 `chat_stream_advanced()`가 거대한 함수로 커지는 것을 막을 수 있습니다.
