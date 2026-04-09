# 🚗 Vehicle Manual RAG Chatbot

차량 사용 매뉴얼(PDF)을 파싱하여 임베딩 기반 RAG(Retrieval-Augmented Generation)를 구성하고,  
이를 기반으로 차량 사용 관련 질의에 응답하는 챗봇 PoC 프로젝트입니다.

> **현재 상태**: 초기 개발 단계 (Backend 아키텍처 구축 완료, Chat/RAG 로직 개발 진행 중)

---

## 기술 스택

| 영역 | 기술 |
|------|------|
| **Backend** | FastAPI, Uvicorn, Pydantic |
| **Database** | Supabase (PostgreSQL + pgvector) |
| **LLM / RAG** | LangChain, LangGraph |
| **Frontend** | HTML (개발 예정) |
| **Infra** | Docker, Helm, GitHub Actions CI |
| **Data Pipeline** | PyMuPDF, Sentence-Transformers, Pandas |

---

## 프로젝트 구조

```
vehicle-manual-bot-LLM-RAG/
├── .github/workflows/          # CI/CD 파이프라인 (backend-ci.yaml)
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── endpoints/      # 라우터 (health.py, chat.py)
│   │   │   └── routes.py       # 라우터 통합 등록
│   │   ├── base/               # 공통 기반 모듈
│   │   │   ├── exceptions.py   # 전역 예외 처리 핸들러
│   │   │   ├── logger.py       # 로깅 설정 (TimedRotatingFileHandler)
│   │   │   └── middleware.py   # 요청/응답 로깅 미들웨어
│   │   ├── core/               # 핵심 설정
│   │   │   ├── config.py       # 환경 변수 관리 (pydantic-settings)
│   │   │   ├── database.py     # Supabase 클라이언트 생성
│   │   │   └── dependencies.py # FastAPI 의존성 주입 (DI)
│   │   ├── repositories/       # DB 통신 전담 계층
│   │   │   └── healthz_repository.py
│   │   ├── schemas/            # Pydantic 데이터 모델 (Request/Response)
│   │   │   ├── response.py     # 통합 응답 규격 (CommonResponse)
│   │   │   ├── healthz.py      # Health Check 요청 스키마
│   │   │   └── chat.py         # Chat 요청/응답 스키마
│   │   ├── services/           # 비즈니스 로직 계층
│   │   │   └── healthz_service.py
│   │   └── main.py             # FastAPI App 팩토리 (lifespan 관리)
│   ├── docs/                   # 차량 매뉴얼 PDF 원본
│   ├── helm/                   # Kubernetes Helm Chart
│   ├── dockerfile              # 컨테이너 빌드 파일
│   ├── requirements.txt        # Python 의존성 목록
│   └── .env.example            # 환경 변수 템플릿
├── frontend/
│   ├── app/                    # 프론트엔드 앱 (개발 예정)
│   └── helm/                   # Frontend Helm Chart
├── mocktest/                   # 데이터 파이프라인 스크립트 (PDF 파싱 → 임베딩 → DB 저장)
└── requirements.txt            # 데이터 파이프라인 의존성
```

---

## 아키텍처 설계 원칙

### 계층형 아키텍처 (Layered Architecture)
요청의 흐름은 철저하게 **Router → Service → Repository** 3단계를 따릅니다.

```
Client Request
    ↓
[Router]        → HTTP 요청 수신, 파라미터 검증, 의존성 주입
    ↓
[Service]       → 비즈니스 로직 처리, 도메인 규칙 판단
    ↓
[Repository]    → DB 쿼리 실행, 데이터 반환
    ↓
Client Response ← CommonResponse 규격으로 통일 응답
```

### 전역 예외 처리 (Global Exception Handler)
`base/exceptions.py`에서 모든 예외를 중앙 관리하여, 각 계층(Router/Service/Repo)에서 `try-except` 없이 코드를 작성할 수 있습니다.

| 예외 타입 | HTTP 상태 코드 | 설명 |
|-----------|----------------|------|
| `HTTPException` | 해당 코드 그대로 | 비즈니스 로직에서 명시적으로 던지는 에러 |
| `RequestValidationError` | 400 | Pydantic 검증 실패 (파라미터 오류) |
| `APIError` (Supabase) | 400 | DB 통신 중 발생하는 에러 |
| `Exception` (전역) | 500 | 예상하지 못한 모든 에러의 최종 방어막 |

### 요청 추적 (Trace ID)
모든 요청에 고유한 `trace_id`를 부여하여, 요청의 시작부터 에러 발생까지 전체 흐름을 하나의 ID로 추적할 수 있습니다.

**동작 방식:**
1. 클라이언트가 `trace-id` 헤더를 보내면 해당 값을 사용합니다.
2. 헤더가 없으면 서버가 `uuid4`로 자동 생성합니다.
3. `request.state.trace_id`에 저장되어 미들웨어 → 예외 핸들러까지 일관되게 전파됩니다.

**로그 출력 예시:**
```
[INFO]  Request: [550e8400-e29b-41d4-a716-446655440000] 127.0.0.1 | POST | /healthz
[INFO]  Response: [550e8400-e29b-41d4-a716-446655440000] 200
[ERROR] [550e8400-e29b-41d4-a716-446655440000] HTTPException -404- Data not found
```

| 계층 | trace_id 활용 |
|------|--------------|
| `middleware.py` | 생성 및 Request/Response 로그에 기록 |
| `exceptions.py` | 모든 예외 핸들러의 에러 로그에 기록 |

### 통합 응답 규격 (CommonResponse)
모든 API 응답은 `CommonResponse` 모델로 감싸서 반환됩니다.

```json
{
  "status_code": 200,
  "message": "요청이 완료되었습니다.",
  "data": { ... }
}
```

---

## 시작하기

### 1. 환경 변수 설정
```bash
cd backend
cp .env.example .env
# .env 파일에 실제 Supabase URL과 Key를 입력합니다.
```

### 2. 의존성 설치 및 실행
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8009 --reload
```

### 3. API 문서 확인
서버 실행 후 브라우저에서 접속:
- **Swagger UI**: http://localhost:8009/docs
- **ReDoc**: http://localhost:8009/redoc

---

## API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| `GET` | `/health` | 서버 생존 확인 (Liveness) |
| `POST` | `/healthz` | DB 연결 상태 확인 (Readiness) |
| `POST` | `/api/v1/chat` | 챗봇 질의 (개발 중) |

---

## 데이터 파이프라인 (mocktest/)

차량 매뉴얼 PDF를 파싱하여 Supabase에 임베딩 데이터를 저장하는 스크립트 모음입니다.

| 파일 | 설명 |
|------|------|
| `01_connection_test.py` | DB 연결 테스트 |
| `06_analyze_new_pdf.py` | PDF 구조 분석 |
| `07_parser_final.py` | 매뉴얼 파싱 (최종 버전) |
| `08_save_manual_embading_db.py` | 임베딩 생성 및 DB 저장 |
| `09_hybrid_search_manual.py` | 하이브리드 검색 테스트 (Vector + FTS) |

---

## Supabase Database 스키마

### models (차량 모델 정보)
```sql
CREATE TABLE vehicle_manual_rag.models (
  model_id    VARCHAR NOT NULL PRIMARY KEY,
  model_nm    VARCHAR NOT NULL,
  lineup_id   VARCHAR NOT NULL,
  gen_no      BIGINT  NOT NULL,
  fuel_type   VARCHAR NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### vehicle_manual (매뉴얼 임베딩 데이터)
```sql
CREATE TABLE vehicle_manual_rag.vehicle_manual (
  id          BIGSERIAL PRIMARY KEY,
  model_name  TEXT NOT NULL,
  heading     TEXT,
  content     TEXT,
  page_num    INTEGER,
  metadata    JSONB,
  embedding   vector,          -- pgvector 확장
  fts         TSVECTOR          -- Full-Text Search
);

-- 인덱스
CREATE INDEX vehicle_manual_fts_idx 
  ON vehicle_manual_rag.vehicle_manual USING gin (fts);

CREATE INDEX vehicle_manual_embedding_idx 
  ON vehicle_manual_rag.vehicle_manual USING hnsw (embedding vector_cosine_ops);
```