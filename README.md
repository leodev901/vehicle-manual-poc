# 🚗 Vehicle Manual RAG Chatbot

> **차량 매뉴얼을 AI가 읽고, 사용자의 질문에 정확하게 답변하는 RAG 기반 인텔리전트 챗봇 서비스입니다.**

> **현재 상태**: ✅ RAG 파이프라인 완성 (Inference Server를 Hugging Face Spaces에 MSA로 분리 배포 완료, 하이브리드 벡터+FTS 검색 연동 완료, SSE 스트리밍 챗봇 엔드포인트 운영 중) | ✅ 프론트엔드 완성 (Next.js App Router 기반 모바일-퍼스트 챗봇 UI, SSE 스트리밍 연동, 차량 Cascade 선택 위젯 구현)

---

## 🎯 서비스 소개 및 목적

### 해결하는 문제 (Problem Statement)

차량을 구매하고 나서 실제로 사용자 매뉴얼을 처음부터 끝까지 읽는 사람은 거의 없습니다.
"에어컨 필터는 어떻게 교체하지?", "이 경고등은 무슨 뜻이지?" 라는 질문이 생겼을 때,
두꺼운 PDF를 뒤지거나 서비스센터에 전화하는 방법은 **너무 불편하고 비효율적**입니다.

**Vehicle Manual RAG Chatbot**은 이 문제를 완벽하게 해결합니다.

### 핵심 기능 (Key Features)

| 기능 | 설명 |
|------|------|
| 🤖 **AI 매뉴얼 검색** | 사용자의 자연어 질문을 AI가 의미적으로 해석하여 매뉴얼에서 가장 관련 있는 내용을 정밀하게 찾아냅니다. |
| ⚡ **실시간 스트리밍 응답** | LLM이 답변을 생성하는 즉시 토큰 단위로 화면에 스트리밍되어, 기다리는 답답함 없이 ChatGPT와 같은 UX를 제공합니다. |
| 🚗 **차종별 개인화 검색** | 현대, 기아 등 브랜드 → 라인업 → 특정 모델(아이오닉5, 투싼 등)을 선택하면 **해당 차종 매뉴얼에서만** 답변을 찾습니다. |
| 🔬 **하이브리드 RAG 검색** | 의미 기반(Vector Semantic Search)과 키워드 일치(Full-Text Search)를 **수학적으로 혼합**하여 어떤 질문에도 정확도 높은 문서를 검색합니다. |
| 🧩 **MSA 마이크로서비스 아키텍처** | 무거운 AI 추론(임베딩)을 독립 서버로 분리하여, 메인 서버는 가볍고 빠르게 유지하면서 각 서비스를 독립적으로 확장 가능합니다. |

---

## 🗺️ 서비스 시나리오 (User Story)

```
[사용자]
  "내 투싼 하이브리드 스마트키 배터리 방전됐는데 어떻게 교체하지?"
  
      ↓ 차량 선택 (현대 → 투싼 → 2024 하이브리드)
      ↓ 자연어 질문 입력
  
[AI 챗봇] (실시간 스트리밍으로 답변 시작)
  "투싼 하이브리드의 스마트키 배터리 교체 방법을 안내드립니다.
   1단계: 스마트키 뒷면의 슬라이드 버튼을 당겨 보조 키를 분리합니다.
   2단계: 동전 등을 이용해 스마트키 케이스를 분리합니다.
   3단계: 기존 CR2032 배터리를 제거하고 동일 규격 신품으로 교체합니다.
   ..."
```

---

## ⚙️ 시스템 동작 흐름 (System Architecture Flow)

```
[1단계: 차량 선택]
사용자 → 브랜드/라인업/모델 API 호출 → Supabase DB에서 목록 조회 → 드롭다운 UI 렌더링

[2단계: 질문 입력 및 키워드 추출]
사용자 질문 입력 → LLM (GPT / Gemini) → 질문의 핵심 의도를 '정제된 질문 1문장'으로 추출

[3단계: 의미 기반 벡터화 (S2S 통신)]
추출된 질문 → Hugging Face (Inference Server) → e5-large 모델로 1024차원 벡터 변환

[4단계: 하이브리드 검색]
생성된 벡터 + 원본 키워드 → Supabase RPC 함수 호출
→ 벡터 유사도(Cosine, 70%) + 키워드 일치(FTS, 30%) 점수 혼합 → Top-K 문서 조각 반환

[5단계: RAG 응답 생성 (실시간 스트리밍)]
검색된 문서 → LLM Context로 주입 → LangChain LCEL 파이프라인 실행
→ 생성되는 토큰을 SSE(Server-Sent Events)로 브라우저에 실시간 전송
→ 사용자 화면에 답변이 실시간으로 타이핑되듯 표시됨
```

---

## 기술 스택

| 영역 | 기술 |
|------|------|
| **Backend** | FastAPI, Uvicorn, Pydantic |
| **Database** | Supabase (PostgreSQL + pgvector) |
| **LLM / RAG** | LangChain, OpenAI, Google GenAI (멀티 모델 지원) |
| **Frontend** | Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS, lucide-react |
| **Infra** | Docker, Helm, GitHub Actions CI |
| **Data Pipeline** | PyMuPDF, Sentence-Transformers, Pandas |

---

## 프로젝트 구조

```
vehicle-manual-bot-LLM-RAG/
├── .github/workflows/          # CI/CD 파이프라인 (backend-ci.yaml)
├── inference_server/           # 🆕 독립 임베딩 추론 서버 (Hugging Face Spaces 배포)
│   ├── main.py                 # FastAPI 임베딩 엔드포인트 (SentenceTransformer e5-large)
│   ├── Dockerfile              # CPU 최적화 컨테이너 빌드 파일
│   ├── requirements.txt        # 추론 서버 전용 의존성
│   └── README.md               # 추론 서버 가이드 및 HF Spaces 배포 방법
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── endpoints/      # 라우터
│   │   │   │   ├── health.py   # 헬스체크 엔드포인트
│   │   │   │   ├── chat.py     # 챗봇 SSE 스트리밍 엔드포인트
│   │   │   │   └── manual.py   # 🆕 차량 브랜드/라인업/모델 조회 엔드포인트
│   │   │   └── routes.py       # 라우터 통합 등록
│   │   ├── base/               # 공통 기반 모듈
│   │   │   ├── exceptions.py   # 전역 예외 처리 핸들러
│   │   │   ├── logger.py       # 로깅 설정 (TimedRotatingFileHandler)
│   │   │   └── middleware.py   # 요청/응답 로깅 미들웨어
│   │   ├── core/               # 핵심 설정
│   │   │   ├── config.py       # 환경 변수 관리 (pydantic-settings, HF_TOKEN 포함)
│   │   │   ├── database.py     # Supabase 클라이언트 생성
│   │   │   └── dependencies.py # FastAPI 의존성 주입 (DI)
│   │   ├── prompts/            # LLM 프롬프트 템플릿 분리 관리
│   │   │   └── chat_prompts.py # 키워드 추출 / RAG 응답 생성 프롬프트
│   │   ├── repositories/       # DB 통신 전담 계층
│   │   │   ├── healthz_repository.py
│   │   │   └── manual_repository.py  # 🆕 브랜드/라인업/모델/RAG 하이브리드 검색
│   │   ├── schemas/            # Pydantic 데이터 모델 (Request/Response)
│   │   │   ├── response.py     # 통합 응답 규격 (CommonResponse)
│   │   │   ├── healthz.py      # Health Check 요청 스키마
│   │   │   ├── chat.py         # Chat 요청/응답 스키마 (LLM 모델 설정 포함)
│   │   │   └── manual.py       # 🆕 Manual 요청 스키마 (Lineup/Model 필터)
│   │   ├── services/           # 비즈니스 로직 계층
│   │   │   ├── chat_service.py # RAG 파이프라인 + SSE 스트리밍 (httpx S2S 임베딩 호출)
│   │   │   ├── manual_service.py    # 🆕 차량 정보 비즈니스 로직 + 예외 처리
│   │   │   └── healthz_service.py
│   │   └── main.py             # FastAPI App 팩토리 (lifespan 관리)
│   ├── docs/                   # 차량 매뉴얼 PDF 원본
│   ├── helm/                   # Kubernetes Helm Chart
│   ├── dockerfile              # 컨테이너 빌드 파일
│   ├── requirements.txt        # Python 의존성 목록
│   └── .env.example            # 환경 변수 템플릿
├── frontend/
│   ├── src/
│   │   ├── app/                # Next.js App Router (layout.tsx, page.tsx, globals.css)
│   │   ├── components/         # UI 컴포넌트 (TopAppBar, VehicleSelectorChip, ChatInterface, ChatInput)
│   │   ├── lib/                # API 호출 함수 (SSE 스트리밍 포함)
│   │   ├── types/              # TypeScript 타입 정의 (백엔드 Pydantic 스키마와 매핑)
│   │   └── instrumentation.ts  # Node.js 서버 사이드 초기화 훅
│   ├── next.config.js          # Next.js 설정 (백엔드 API 프록시 rewrites)
│   ├── tailwind.config.js      # Tailwind CSS (Mint Breeze 디자인 시스템 토큰)
│   ├── package.json
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
[Router]        → HTTP 요청 수신, 파라미터 검증 (비동기 처리)
    ↓ (Depends()를 통한 Class DI 주입)
[Service]       → 비즈니스 로직 처리, LCEL 체인 실행 및 Streaming (yield)
    ↓ (AsyncClient 주입)
[Repository]    → DB 비동기 쿼리 실행, 데이터 반환
    ↓
Client Response ← CommonResponse 규격 또는 실시간 StreamingResponse(SSE) 반환
```
### 🧩 마이크로서비스 (MSA) 분리: Inference Server (추론 서버)
메인 웹 API 서버의 확장성과 가용성을 극대화하기 위해, 무거운 AI 연산을 전담하는 별도의 **추론 전용 마이크로서비스(`inference_server/`)**를 분리하여 오케스트레이션합니다.

* **관심사 분리 (SRP)**: 2GB가 넘는 대용량 PyTorch `SentenceTransformer` (e5-large) 모델의 로딩과 벡터 연산을 추론 서버가 100% 전담합니다.
* **S2S (Server-to-Server) 통신**: 메인 백엔드(`chat_service.py`)가 내부망에서 `httpx`를 이용해 추론 서버와 안전하게 비동기 통신합니다. 웹 브라우저의 직접 호출이 차단되므로 **CORS 에러로부터 완전히 자유롭고, 악의적인 외부 공격으로부터 안전**합니다.
* **무료 인프라 극대화 (Hugging Face Spaces)**: 
  * 메모리를 독식하는 추론 엔진은 RAM 16GB를 무료로 제공하는 **Hugging Face Spaces (Docker)** 환경에 격리하여 배포합니다.
  * 추론 엔진이 떨어져 나간 메인 백엔드 서버는 사이즈가 극적으로 가벼워져, 향후 Vercel이나 Render 같은 무료 클라우드에서도 무한에 가까운 API 워커(Worker) 스케일링이 가능합니다.

### 비동기(Async) 의존성 주입 (Class-based DI)
엔터프라이즈 환경에서의 테스트 용이성(Mocking)과 코드 유지보수성을 위해 FastAPI의 강력한 **의존성 주입(Dependency Injection)** 시스템을 활용합니다.
* **Singleton 객체 관리**: 무거운 DB/LLM 연결 객체는 `main.py`의 `lifespan` 시점에서 단 1회만 비동기로 생성(`app.state`에 저장)됩니다.
* **Class `__init__` DI**: 라우터에서 함수 파라미터로 무분별하게 객체를 넘기는 패턴(Parameter Explosion)을 방지하고, Service나 Repository 클래스 생성 시점에 `Depends()`를 통해 필요한 컴포넌트만 깔끔하게 주입받습니다.

### 실시간 응답 스트리밍 (Server-Sent Events)
답변 생성이 오래 걸리는 LLM의 단점을 극복하고 뛰어난 UX를 제공하기 위해 **SSE(Server-Sent Events)** 방식을 채택했습니다.
* LangChain의 `.astream()`을 사용하여 LLM이 예측한 토큰(조각)을 생성 즉시 클라이언트 브라우저로 전송(`yield`)합니다.
* 프론트엔드가 진행 상태를 알 수 있도록 `{"status": "processing", "message": "키워드 추출 중..."}` 과 같은 상태 값(Status)을 혼합하여 스트리밍합니다.

### 멀티 모델 지원 & LCEL (LangChain Expression Language) 체제
특정 LLM 벤더(OpenAI, Google)에 귀속되지 않는 범용적 챗봇을 설계했습니다.

* **Registry 패턴 지원**: `core/llm.py`에서 등록 가능한 여러 모델(Raw SDK 및 LangChain ChatModel)을 딕셔너리 형태로 띄워 두고 DI로 주입받습니다.
* **투트랙 전략 (`chat_service.py`)**:
  * `chat()`: 각 제조사의 고유 파이썬 SDK 문법을 기반으로 분기(`if/elif`)하여 처리하는 로직
  * `chat_langchain()`: LangChain의 **LCEL(`prompt | llm | parser`)** 문법을 활용, 제조사 인터페이스 차이를 흡수하고 단일화된 파이프라인으로 처리.

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
| `POST` | `/api/v1/chat` | 챗봇 질의 (Raw SDK 기반 멀티 모델 단건 응답) |
| `POST` | `/api/v1/chat/langchain` | 챗봇 질의 (LangChain LCEL 기반 단일 파이프라인 단건 응답) |
| `POST` | `/api/v1/chat/stream` | 실시간 챗봇 질의 (LangChain LCEL 기반 SSE 스트리밍 응답) |
| `GET` | `/api/v1/manual/brands` | 🆕 차량 브랜드 목록 조회 |
| `GET` | `/api/v1/manual/lineups?brand_id=HD` | 🆕 브랜드별 라인업 목록 조회 |
| `GET` | `/api/v1/manual/models?lineup_id=LX3` | 🆕 라인업별 차량 모델 목록 조회 |

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

### 1. brands (차량 브랜드 정보)
```sql
create table vehicle_manual_rag.brands (
  brand_id character varying not null,
  brand_nm character varying not null,
  created_at timestamp with time zone not null default now(),
  updated_at timestamp with time zone null default now(),
  constraint brands_pkey primary key (brand_id)
) TABLESPACE pg_default;
```

### 2. lineups (차량 라인업 정보)
```sql
create table vehicle_manual_rag.lineups (
  lineup_id character varying not null default ''::character varying,
  lineup_nm character varying not null,
  brand_id character varying not null,
  type character varying null,
  created_at timestamp with time zone not null default now(),
  updated_at timestamp with time zone not null default now(),
  constraint lineups_pkey primary key (lineup_id),
  constraint lineups_brand_id_fkey foreign KEY (brand_id) references vehicle_manual_rag.brands (brand_id)
) TABLESPACE pg_default;
```

### 3. models (차량 모델 정보)
```sql
create table vehicle_manual_rag.models (
  model_id character varying not null,
  model_nm character varying not null,
  lineup_id character varying not null,
  gen_no bigint not null,
  fuel_type character varying not null,
  created_at timestamp with time zone not null default now(),
  updated_at timestamp with time zone not null default now(),
  constraint models_pkey primary key (model_id),
  constraint models_lineup_id_fkey foreign KEY (lineup_id) references vehicle_manual_rag.lineups (lineup_id)
) TABLESPACE pg_default;
```

### 4. vehicle_manual (매뉴얼 임베딩 데이터)
```sql
create table vehicle_manual_rag.vehicle_manual (
  id bigserial not null,
  model_id character varying not null,
  heading text null,
  content text null,
  page_num integer null,
  metadata jsonb null,
  embedding extensions.vector null,
  fts tsvector null,
  constraint vehicle_manual_pkey primary key (id),
  constraint vehicle_manual_model_id_fkey foreign KEY (model_id) references vehicle_manual_rag.models (model_id)
) TABLESPACE pg_default;

-- 인덱스 및 트리거
create index IF not exists vehicle_manual_fts_idx 
  on vehicle_manual_rag.vehicle_manual using gin (fts) TABLESPACE pg_default;

create index IF not exists vehicle_manual_embedding_idx 
  on vehicle_manual_rag.vehicle_manual using hnsw (embedding extensions.vector_cosine_ops) TABLESPACE pg_default;

create trigger tsvectorupdate BEFORE INSERT or update 
  on vehicle_manual_rag.vehicle_manual for EACH row
  execute FUNCTION vehicle_manual_rag.update_fts ();
```


### 5. 하이브리드 검색 함수 (Supabase RPC)
```sql
-- Arguments:
-- query_text (text): 사용자가 입력한 검색어 원문 (키워드/문장)
-- query_embedding (vector): 사용자가 입력한 검색어를 임베딩(숫자 배열)으로 변환한 값
-- match_count (integer): 반환받을 최대 문서 조각 개수 (Top-K)
-- filter_model (character varying): 필터링할 특정 차량 모델 ID
-- full_text_weight (double): 키워드 일치 검색(FTS) 반영 가중치 비율 (예: 0.3)
-- semantic_weight (double): 의미 기반 검색(Vector) 반영 가중치 비율 (예: 0.7)

begin
  return query (
    select *
    from vehicle_manual_rag.vehicle_manual
    where model_id = filter_model  -- 특정 차량 모델(예: 아이오닉5)로만 범위 한정
    order by
      -- 1. 의미적 유사도 점수 (Semantic Search)
      (semantic_weight * (1 - (vehicle_manual_rag.vehicle_manual.embedding <=> query_embedding))) +
      
      -- 2. 키워드 일치 점수 (Full-Text Search)
      -- [수정된 부분] to_tsquery -> websearch_to_tsquery 로 변경!
      -- 이유: 일반 to_tsquery는 사용자가 '배터리 교체'처럼 띄어쓰기를 입력하면 Syntax Error가 발생합니다.
      -- websearch_to_tsquery를 쓰면 구글 검색처럼 자연어 띄어쓰기를 유연하게 파싱하므로 오류를 원천 차단합니다.
      (full_text_weight * (ts_rank(vehicle_manual_rag.vehicle_manual.fts, websearch_to_tsquery('simple', query_text)))) desc
      
    limit match_count
  );
end;
```

#### 💡 [설명] 하이브리드 RAG 검색(Hybrid Search) 동작 원리
이 SQL 함수는 데이터베이스에서 데이터를 "단순히 찾아오는 것"을 넘어, **두 가지 검색 점수를 수학적으로 혼합(Fusion)하여 순위를 매기는 핵심 RAG 엔진**입니다.

1. **상호보완적 검색**:
   * **Semantic Search (`<=> query_embedding`)**: 문맥(의미)을 이해합니다. 원본 문서에 '배터리'라는 단어가 없어도, 의미상 가까운 '방전'이라는 내용이 있다면 찾아냅니다. (코사인 유사도 거리 연산)
   * **Full-Text Search (`ts_rank`)**: 단어의 일치도를 봅니다. '에러코드 E04' 처럼 정확하고 고유한 키워드가 포함된 문서를 절대 놓치지 않습니다.
2. **수학적 가중치 결합 (Weight Combination)**:
   * 두 점수에 각각 가중치(`semantic_weight`, `full_text_weight`)를 곱해 더합니다. 보통 벡터(의미)를 **0.7**, 키워드 검색을 **0.3**으로 조절하여 두 검색 기법의 장점만 취합니다.
3. **오류 방지 설계 (websearch_to_tsquery)**:
   * 사용자가 입력한 날것의 문자열(특수문자, 띄어쓰기 등)을 파싱하다 에러가 나는 것을 막기 위해 `websearch_to_tsquery`를 도입하여 시스템 안정성이 크게 올라갔습니다.
4. **가중치 분배(Alpha Tuning)와 한계점 (RRF의 필요성)**:
   * 두 가중치의 합을 1.0(예: 0.7 + 0.3)으로 맞추는 것이 업계 표준입니다. 이를 통해 "이번 검색은 의미에 70%, 키워드에 30% 비중을 둔다"는 직관적 제어가 가능합니다.
   * **[엔터프라이즈 고도화 포인트]** 코사인 유사도 점수는 0~1 사이로 정규화되지만, `ts_rank`는 문서 길이에 따라 점수가 한계 없이 치솟을 수 있습니다. 따라서 추후 고도화 단계에서는 원시 점수의 곱셈 합산 방식을 뛰어넘어, 두 검색 결과의 **'등수(Rank)'**를 기반으로 융합하는 **RRF(Reciprocal Rank Fusion)** 기법으로 발전시킬 예정입니다.