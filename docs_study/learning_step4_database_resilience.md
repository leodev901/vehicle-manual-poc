# 4단계 학습 노트: 데이터베이스 생존기 및 폭주 제어

## 1. 이번 단계의 목표

4단계의 핵심은 "서버가 많아질수록 더 안전해지는가?"를 확인하는 것입니다.
FastAPI 서버를 여러 워커와 여러 Pod로 늘리면 API 처리량은 늘어납니다. 하지만 각 워커가 DB 커넥션 풀을 따로 가지면, DB 입장에서는 연결 수가 폭발적으로 증가할 수 있습니다.

```text
사용자 트래픽 증가
    ↓
FastAPI Pod 증가
    ↓
Gunicorn Worker 증가
    ↓
각 Worker마다 SQLAlchemy Pool 생성
    ↓
PostgreSQL/Supabase 연결 수 고갈
    ↓
Too many connections
```

그래서 4단계에서는 아래 두 가지를 실습합니다.

| 구분 | 실습 주제 | 목적 |
|---|---|---|
| 4-1 | DB 커넥션 풀 한계와 PgBouncer | 서버 확장 시 DB 연결 폭주를 막는다 |
| 4-2 | 외부 API 방어막과 캐싱 | LLM/임베딩 API 장애와 비용 폭주를 막는다 |

---

## 2. 현재 프로젝트의 DB 연결 구조

현재 백엔드는 `backend/app/core/database.py`에서 SQLAlchemy Async Engine을 앱 시작 시 한 번 생성합니다.

```python
engine = create_async_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_recycle=settings.db_pool_recycle,
    echo=settings.db_echo,
    connect_args={
        "prepared_statement_cache_size": 0,
        "statement_cache_size": 0,
    },
)
```

### 왜 `pool_size`와 `max_overflow`가 중요한가?

SQLAlchemy는 DB 연결을 매 요청마다 새로 만들지 않고 풀에 보관했다가 재사용합니다.

| 설정 | 의미 |
|---|---|
| `pool_size` | 평상시 유지할 기본 커넥션 수 |
| `max_overflow` | 순간적으로 추가 허용할 임시 커넥션 수 |
| `pool_recycle` | 오래된 커넥션을 재생성하는 주기 |

현재 기본 설정은 `backend/app/core/config.py` 기준으로 아래와 같습니다.

```text
db_pool_size = 10
db_max_overflow = 20
```

즉, 워커 1개당 최대 DB 커넥션은 아래처럼 계산합니다.

```text
워커 1개당 최대 커넥션 수 = pool_size + max_overflow
                         = 10 + 20
                         = 30
```

---

## 3. 확장 시 DB 커넥션 수 계산

중요한 점은 SQLAlchemy Engine이 "프로세스마다" 생성된다는 것입니다.
Gunicorn Worker는 각각 별도 프로세스이므로, Worker 수가 늘어나면 커넥션 풀도 Worker 수만큼 늘어납니다.

```text
최대 DB 커넥션 수
= Pod 수 × Worker 수 × (pool_size + max_overflow)
```

예를 들어 현재 Helm 설정이 아래와 같다고 가정합니다.

```text
HPA maxReplicas = 5
Gunicorn worker = 1
pool_size = 10
max_overflow = 20
```

그러면 최대 DB 커넥션 수는 다음과 같습니다.

```text
5 × 1 × (10 + 20) = 150
```

만약 worker를 4개로 늘리면 어떻게 될까요?

```text
5 × 4 × (10 + 20) = 600
```

API 서버 입장에서는 "워커만 늘렸을 뿐"이지만, DB 입장에서는 연결 요청이 4배로 늘어납니다.
이것이 PgBouncer를 배우는 이유입니다.

---

## 4. PgBouncer가 필요한 이유

PgBouncer는 애플리케이션과 PostgreSQL 사이에 두는 커넥션 프록시입니다.

```text
FastAPI Worker
FastAPI Worker
FastAPI Worker
    ↓ 많은 연결 요청
PgBouncer
    ↓ 제한된 실제 DB 연결
PostgreSQL / Supabase
```

애플리케이션은 PgBouncer에 연결하고, PgBouncer가 실제 DB 연결을 적은 수로 재사용합니다.
이렇게 하면 서버가 늘어나도 DB에 직접 붙는 커넥션 수를 제어할 수 있습니다.

### PgBouncer는 "설정 옵션"이 아니라 별도 서버입니다

중요한 점이 있습니다.
`prepared_statement_cache_size = 0`을 설정했다고 해서 PgBouncer를 사용한 것은 아닙니다.

PgBouncer는 Python 코드 안의 옵션이 아니라, PostgreSQL 앞단에 떠 있는 별도의 커넥션 프록시 서버입니다.

```text
PgBouncer를 사용하지 않는 구조

FastAPI Worker 1 ───────┐
FastAPI Worker 2 ───────┤
FastAPI Worker 3 ───────┼──> PostgreSQL / Supabase DB
FastAPI Worker 4 ───────┤
FastAPI Worker N ───────┘

각 Worker가 DB에 직접 연결합니다.
Worker/Pod가 늘어날수록 DB가 직접 받아야 하는 연결 수도 같이 늘어납니다.
```

```text
PgBouncer를 사용하는 구조

FastAPI Worker 1 ───────┐
FastAPI Worker 2 ───────┤
FastAPI Worker 3 ───────┼──> PgBouncer ──> PostgreSQL / Supabase DB
FastAPI Worker 4 ───────┤       │
FastAPI Worker N ───────┘       │
                                └─ 실제 DB 연결 수를 제한하고 재사용
```

즉, 애플리케이션 입장에서는 연결 대상이 PostgreSQL에서 PgBouncer로 바뀝니다.

```text
기존 직접 연결:
DATABASE_URL=postgresql+asyncpg://user:password@db.xxx.supabase.co:5432/postgres

PgBouncer/Pooler 연결:
DATABASE_URL=postgresql+asyncpg://user:password@pooler.xxx.supabase.com:6543/postgres
```

프로젝트에서 `prepared_statement_cache_size = 0`을 설정한 것은 "PgBouncer를 이미 사용했다"는 뜻이 아닙니다.
정확히는 "나중에 PgBouncer를 붙였을 때 충돌이 덜 나도록 asyncpg의 prepared statement cache를 꺼둔 것"입니다.

---

## 4-1. PgBouncer를 안 쓰면 무슨 일이 생기는가?

SQLAlchemy의 커넥션 풀은 Worker 프로세스마다 따로 생깁니다.
현재 기본값은 Worker 1개당 최대 30개입니다.

```text
pool_size = 10
max_overflow = 20

Worker 1개당 최대 연결 = 30
```

Pod와 Worker가 늘어나면 전체 연결 수는 아래처럼 커집니다.

```text
최대 DB 연결 수 = Pod 수 × Worker 수 × (pool_size + max_overflow)
```

예를 들어 HPA로 Pod가 5개까지 늘고, 각 Pod 안에 Gunicorn worker가 4개라면:

```text
5 Pods × 4 Workers × 30 Connections = 600 Connections
```

그림으로 보면 이렇습니다.

```text
                 ┌──────────── Pod 1 ────────────┐
                 │ Worker 1: Pool max 30          │
                 │ Worker 2: Pool max 30          │
Client Traffic ─▶│ Worker 3: Pool max 30          │
                 │ Worker 4: Pool max 30          │
                 └────────────────────────────────┘
                                │ 120 connections
                                ▼
                 ┌──────────── Pod 2 ────────────┐
                 │ Worker 1: Pool max 30          │
                 │ Worker 2: Pool max 30          │
                 │ Worker 3: Pool max 30          │
                 │ Worker 4: Pool max 30          │
                 └────────────────────────────────┘
                                │ 120 connections
                                ▼
                              ...
                                ▼
                 ┌──────────── Pod 5 ────────────┐
                 │ Worker 1: Pool max 30          │
                 │ Worker 2: Pool max 30          │
                 │ Worker 3: Pool max 30          │
                 │ Worker 4: Pool max 30          │
                 └────────────────────────────────┘
                                │ 120 connections
                                ▼
                  PostgreSQL / Supabase DB

총합: 120 × 5 = 600개 연결 가능
```

이때 PostgreSQL의 허용 연결 수가 200개라면, 앱 서버는 정상적으로 확장된 것처럼 보여도 DB는 먼저 한계에 도달합니다.

```text
API 서버 확장 성공
DB 연결 수 폭증
DB max_connections 초과
요청 실패
```

---

## 4-2. PgBouncer를 쓰면 무엇이 달라지는가?

PgBouncer는 앱에서 들어오는 많은 연결을 받아서, 실제 PostgreSQL 연결은 더 적은 수로 재사용합니다.

```text
앱 연결 관점

FastAPI Worker들이 PgBouncer에 많이 붙음
    ↓
PgBouncer가 요청을 큐잉하고 실제 DB 연결을 재사용
    ↓
PostgreSQL은 제한된 수의 연결만 받음
```

```text
                 ┌──────────── Pod 1 ────────────┐
                 │ Worker 1                       │
                 │ Worker 2                       │
Client Traffic ─▶│ Worker 3                       │
                 │ Worker 4                       │
                 └────────────────────────────────┘
                                │
                 ┌──────────── Pod 2 ────────────┐
                 │ Worker 1                       │
                 │ Worker 2                       │
                 │ Worker 3                       │
                 │ Worker 4                       │
                 └────────────────────────────────┘
                                │
                              ...
                                │
                 ┌──────────── Pod 5 ────────────┐
                 │ Worker 1                       │
                 │ Worker 2                       │
                 │ Worker 3                       │
                 │ Worker 4                       │
                 └────────────────────────────────┘
                                │
                                ▼
                        ┌──────────────┐
                        │  PgBouncer   │
                        │              │
                        │ client conn  │  ← 앱 연결은 많이 받음
                        │ server conn  │  ← DB 연결은 제한
                        └──────────────┘
                                │
                                ▼
                       PostgreSQL / Supabase DB
```

비유하면 PgBouncer는 식당 앞의 대기 관리자와 비슷합니다.

```text
손님 300명 = FastAPI 요청/커넥션
테이블 30개 = 실제 DB 커넥션
대기 관리자 = PgBouncer
```

손님이 300명 왔다고 테이블 300개를 만들 수는 없습니다.
대신 대기 관리자가 30개 테이블을 빠르게 회전시켜 전체 손님을 처리합니다.
PgBouncer도 마찬가지로 실제 DB 연결을 무한히 늘리지 않고 재사용합니다.

---

## 4-3. PgBouncer Pooling Mode

PgBouncer에는 대표적으로 세 가지 pooling mode가 있습니다.

| Mode | 실제 DB 연결을 언제 반환하나? | 특징 |
|---|---|---|
| Session pooling | 클라이언트 연결이 끝날 때 | 호환성은 좋지만 연결 절감 효과는 상대적으로 작음 |
| Transaction pooling | 트랜잭션이 끝날 때 | 연결 절감 효과가 좋고 Supabase Pooler에서 흔히 사용 |
| Statement pooling | SQL 문 하나가 끝날 때 | 제약이 많아 일반 앱에서는 신중히 사용 |

실무에서 많이 만나는 것은 `transaction pooling`입니다.
이 모드에서는 트랜잭션이 끝나면 PgBouncer가 실제 DB 세션을 다른 클라이언트에게 바로 빌려줄 수 있습니다.

```text
Transaction Pooling

Request A ── BEGIN ── SELECT ── COMMIT ──┐
                                         │ DB 세션 반환
Request B ───────────── BEGIN ── SELECT ─┘ 같은 DB 세션 재사용 가능
```

이 방식은 연결 수를 줄이는 데 효과적이지만, "내가 같은 DB 세션을 계속 잡고 있다"는 가정이 깨집니다.

---

## 5. PgBouncer와 Prepared Statement 이슈

현재 `database.py`에는 아래 옵션이 이미 들어가 있습니다.

```python
connect_args={
    "prepared_statement_cache_size": 0,
    "statement_cache_size": 0,
}
```

이 설정은 PgBouncer의 transaction pooling 모드에서 자주 발생하는 prepared statement 충돌을 줄이기 위한 설정입니다.

### 왜 필요한가?

일반 PostgreSQL 연결은 한 클라이언트가 한 서버 세션을 계속 붙잡는다고 가정합니다.
하지만 PgBouncer의 transaction pooling은 트랜잭션이 끝날 때마다 실제 DB 세션을 다른 클라이언트에게 재사용할 수 있습니다.

이때 클라이언트가 "전에 만들어둔 prepared statement가 아직 있을 것"이라고 기대하면 문제가 생깁니다.

```text
요청 A: prepared statement 생성
트랜잭션 종료
PgBouncer가 실제 DB 세션을 다른 요청에 재사용
요청 A 다음 호출: 이전 statement를 기대
    ↓
prepared statement does not exist / already exists 계열 오류 가능
```

그래서 asyncpg의 statement cache를 끄는 설정이 PgBouncer 호환성에 도움이 됩니다.

### 이 설정을 한 것과 안 한 것의 차이

현재 설정:

```python
connect_args={
    "prepared_statement_cache_size": 0,
    "statement_cache_size": 0,
}
```

이 설정의 의미는 다음과 같습니다.

```text
asyncpg야,
SQL을 prepared statement로 캐싱해두고 재사용하려고 하지 마.
매번 일반 실행에 가깝게 처리해서 PgBouncer transaction pooling과 충돌하지 않게 해줘.
```

설정하지 않았을 때 생길 수 있는 문제는 아래와 같습니다.

```text
1. Request A가 DB 세션 #1에서 prepared statement S_1을 만든다.
2. 트랜잭션이 끝난다.
3. PgBouncer가 DB 세션 #1을 Request B에게 빌려준다.
4. Request A의 다음 쿼리는 "S_1이 아직 있겠지"라고 기대한다.
5. 하지만 실제로는 다른 세션을 받았거나, 같은 이름의 statement 상태가 다를 수 있다.
6. prepared statement 관련 오류가 발생할 수 있다.
```

대표적으로 아래 계열의 오류가 날 수 있습니다.

```text
prepared statement "..." does not exist
prepared statement "..." already exists
DuplicatePreparedStatementError
InvalidSQLStatementNameError
```

그림으로 보면 이렇습니다.

```text
캐시를 켠 상태에서 PgBouncer transaction pooling 사용

FastAPI / asyncpg
    │
    │ "전에 만든 prepared statement S_1 다시 써야지"
    ▼
PgBouncer
    │
    │ 트랜잭션마다 실제 DB 세션을 바꿔 끼울 수 있음
    ▼
PostgreSQL Session A  ── S_1 있음
PostgreSQL Session B  ── S_1 없음
PostgreSQL Session C  ── S_1 이름 충돌 가능

결과: asyncpg의 기대와 실제 DB 세션 상태가 어긋날 수 있음
```

```text
캐시를 끈 상태

FastAPI / asyncpg
    │
    │ "이전 DB 세션 상태를 기대하지 않음"
    ▼
PgBouncer
    │
    │ 어떤 DB 세션을 재사용해도 충돌 가능성이 줄어듦
    ▼
PostgreSQL

결과: PgBouncer transaction pooling과 더 잘 맞음
```

정리하면 다음과 같습니다.

| 구분 | PgBouncer 사용 여부 | prepared statement cache 0 여부 | 의미 |
|---|---|---|---|
| 현재 프로젝트 상태 | 아직 직접 연결일 수 있음 | 적용됨 | PgBouncer 호환 준비 완료 |
| 직접 DB 연결 + cache 켜짐 | 미사용 | 미적용 | 성능상 이점은 있을 수 있으나 PgBouncer 전환 시 충돌 가능 |
| PgBouncer + cache 켜짐 | 사용 | 미적용 | transaction pooling에서 prepared statement 오류 가능 |
| PgBouncer + cache 꺼짐 | 사용 | 적용 | 호환성이 좋아짐 |

즉, 이 설정은 PgBouncer 자체가 아니라 **PgBouncer를 안전하게 쓰기 위한 드라이버 호환 설정**입니다.

---

## 6. 4-1 실습 순서

### Step 1. 현재 최대 커넥션 수 계산

현재 설정값을 기준으로 최대 커넥션 수를 계산합니다.

```text
max_connections_from_app = replicas × workers × (pool_size + max_overflow)
```

현재 기본값 기준:

```text
5 × 1 × (10 + 20) = 150
```

### Step 2. 부하 재현용 엔드포인트 선정

DB 연결을 실제로 사용하는 엔드포인트가 필요합니다.
현재 프로젝트에서는 아래 엔드포인트가 SQLAlchemy 세션을 사용합니다.

```http
POST /health_check
```

요청 예시는 다음과 같습니다.

```json
{
  "schema_name": "vehicle_manual_rag",
  "table_name": "models"
}
```

### Step 3. 동시 요청 부하를 걸어본다

로컬 또는 개발 환경에서 `hey`, `wrk`, `ab` 같은 도구로 동시 요청을 넣습니다.

```bash
hey -n 1000 -c 100 -m POST \
  -H "Content-Type: application/json" \
  -d '{"schema_name":"vehicle_manual_rag","table_name":"models"}' \
  http://localhost:8080/health_check
```

| 옵션 | 의미 |
|---|---|
| `-n 1000` | 총 1000번 요청 |
| `-c 100` | 동시에 100개 요청 |
| `-m POST` | POST 메서드 사용 |

### Step 4. 관측 포인트 확인

부하 테스트 중 아래 값을 확인합니다.

| 위치 | 확인할 것 |
|---|---|
| FastAPI 로그 | 응답 지연, 500 에러, pool timeout |
| Supabase/PostgreSQL | active connection 수 |
| Grafana 로그 | `trace_id`별 실패 요청 |
| 클라이언트 결과 | p95/p99 latency, non-2xx 비율 |

### Step 5. 실습 결과 기록

아래는 로컬 `uvicorn` 단일 프로세스 환경에서 `/health_check`에 부하를 준 결과입니다.

```bash
hey -n 5000 -c 300 -m POST \
  -H "Content-Type: application/json" \
  -d '{"schema_name":"vehicle_manual_rag","table_name":"models"}' \
  http://localhost:8001/health_check
```

![hey 부하 테스트 결과](./img/step4_hey_test.png)

| 항목 | 결과 |
|---|---:|
| 총 요청 수 | 5000 |
| 동시 요청 수 | 300 |
| 전체 소요 시간 | 66.5260s |
| 평균 응답 시간 | 4.0086s |
| 처리량 | 72.1523 req/s |
| p95 latency | 4.2271s |
| p99 latency | 5.1179s |
| 가장 느린 응답 | 7.9464s |
| 200 응답 수 | 4800 |

### 결과 해석

`1000 -c 100` 테스트에서는 모든 요청이 200으로 성공했고 평균 응답 시간도 약 1.4초였습니다.
하지만 `5000 -c 300`으로 올리자 평균 응답 시간이 약 4초까지 늘어났고, p99는 5초를 넘었습니다.

```text
1000 -c 100 → 평균 약 1.4초, 200 응답 1000개
5000 -c 300 → 평균 약 4.0초, 200 응답 4800개
```

이 결과는 "동시 요청 수가 늘어나면 DB를 사용하는 API의 대기 시간이 눈에 띄게 증가한다"는 것을 보여줍니다.
특히 DNS, request write, response read 시간은 거의 작고, 대부분의 시간이 `resp wait`에 몰려 있습니다.
즉, 클라이언트가 서버의 처리 완료를 기다린 시간이 전체 지연의 대부분입니다.

```text
resp wait 평균: 약 4.0024s
```

여기서 `200 응답 수`가 4800개로 보이는 점도 중요합니다.
총 요청은 5000개였으므로, 나머지 200개가 어떤 상태였는지 `hey` 출력의 `Error distribution` 또는 서버 로그를 함께 확인해야 합니다.

확인해야 할 대표 신호는 아래와 같습니다.

| 신호 | 의미 |
|---|---|
| `Error distribution`에 timeout 표시 | 서버나 DB 대기가 길어져 클라이언트가 포기한 요청 |
| 500 응답 증가 | 애플리케이션 또는 DB 연결 계층에서 예외 발생 |
| `QueuePool limit ... timeout` | SQLAlchemy 커넥션 풀 대기 초과 |
| `too many connections` | DB 서버의 실제 연결 한도 초과 |

---

## 7. 4-1 완료 기준

아래를 설명할 수 있으면 4-1은 완료입니다.

- [ ] 왜 Worker 수를 늘리면 DB 커넥션도 같이 늘어나는지 설명할 수 있다.
- [ ] `pool_size`, `max_overflow`, `replicas`, `workers`로 최대 커넥션 수를 계산할 수 있다.
- [ ] PgBouncer가 왜 필요한지 설명할 수 있다.
- [ ] PgBouncer 사용 시 prepared statement cache를 왜 끄는지 설명할 수 있다.
- [ ] 부하 테스트로 DB 연결 병목을 관측할 수 있다.

---

## 8. 다음 실습 예고: 4-2 외부 API 방어막

4-2에서는 `/api/v1/chat/stream/advanced` 흐름을 기준으로 외부 API 장애를 방어합니다.

대상 외부 의존성은 아래와 같습니다.

| 구간 | 외부 의존성 | 장애 예시 |
|---|---|---|
| 키워드 추출 | OpenAI/Gemini/Grok | LLM API 장애, rate limit |
| 임베딩 생성 | Hugging Face Inference Server | cold start, timeout, 5xx |
| RAG 검색 | Supabase RPC | DB 부하, connection timeout |
| 최종 답변 생성 | OpenAI/Gemini/Grok | 긴 응답, stream 중단 |

방어 전략은 아래 순서로 진행합니다.

1. Timeout 명시
2. Retry 정책
3. Circuit Breaker
4. Provider fallback
5. Redis semantic cache
