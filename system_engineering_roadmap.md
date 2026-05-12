# 대용량 트래픽 처리를 위한 시스템 엔지니어링 로드맵 🚀

FastAPI 기반의 어플리케이션을 넘어서, 수만 명의 트래픽을 견디는 엔터프라이즈 시스템 엔지니어로 성장하기 위한 실전 실습형 로드맵입니다.

---

## ✅ 0단계: 고급 어플리케이션 아키텍처 (객체 지향의 꽃: Protocol / ABC) — 완료
인프라를 확장하기 전에, 코드가 어떤 DB나 외부 서비스로 교체되더라도 절대 무너지지 않는 "결합도 0%"의 상태를 만드는 파이썬 심화 설계 기법입니다.

- [x] **비동기 의존성 주입 (Class-based DI)**: `Depends()` 객체 주입 및 파라미터 결합도 제거 (✅ **완료**)
- [x] **추상화(Abstraction)와 다형성**: `typing.Protocol` 기반 DIP 적용. Service → Protocol만 바라보도록 의존성 역전. 도메인 중심 Repository 폴더 구조 확립 (`repositories/manual/`, `repositories/chat/` 등) (✅ **완료**)
- [x] **테스트 주도 개발 (Testable Architecture)**: `ManualMockRepository`, `ManualSqlAlchemyRepository` 생성. `tests/test_manual_service.py` 작성 완료. pytest 환경 구성 (✅ **완료**)
  > 📖 학습 노트: `docs_study/learning_step0_abstraction.md`

## ✅ 1단계: 어플리케이션 레벨의 최적화 (단일 서버 성능 쥐어짜기) — 완료
가장 먼저, 작성한 코드가 서버 성능을 100% 끌어내고 있는지 확인합니다.

- [x] **비동기 이벤트 루프 최적화**: 동기 I/O 블로킹 제거 및 `ainvoke()` 적용 (✅ **완료**)
- [x] **실시간 스트리밍 (SSE)**: Chunk 실시간 `yield` 기술 적용 (✅ **완료**)
- [x] **Gunicorn + Uvicorn Worker**: `gunicorn_conf.py` 생성. `values.yaml → configmap → ENV` 주입 구조 완성. `dockerfile` CMD 교체. `requirements.txt` gunicorn 21.2.0 추가 (✅ **완료**)
- [x] **동기/비동기 차이 이해**: CPU 블로킹 연산 분리 전략 이해. 임베딩 → 외부 HF 서버로 분리하여 이벤트 루프 블로킹 0 달성 (✅ **완료**)
- [x] **uvloop 적용**: `app/main.py`에 플랫폼 조건부 적용. `requirements.txt`에 `uvloop; sys_platform != "win32"` 추가 (✅ **완료**)
  > 📖 학습 노트: `docs_study/learning_step1_gunicorn_uvicorn.md`

## ✅ 2단계: 컨테이너와 패키징 (Docker) — 완료
1. **엔터프라이즈급 Dockerfile 작성법**
   - [x] Multi-stage 빌드 전략으로 이미지 경량화 및 보안 강화 (✅ **완료**)
   - [x] Rootless 컨테이너 설정으로 보안 위험 최소화 (✅ **완료**)
   > 📖 학습 노트: `docs_study/learning_step2_dockerfile_multistage.md`

2. **다중 환경 연동 (Docker Compose)**
   - [x] Backend, Frontend, Redis를 묶는 `docker-compose.yml` 생성 (✅ **완료**)
   - [x] 로컬 개발 환경에서의 서비스 네트워킹 가이드 작성 (✅ **완료**)
   > 📖 학습 노트: `docs_study/learning_step2-2_docker_compose.md`

## ✅ 3단계: 인프라 오케스트레이션 (Kubernetes) — 완료
1. **상태 진단과 자가 치유 (Probes)**
   - [x] Liveness/Readiness Probe 최적화 (`periodSeconds: 720` → `30/10` 수정) (✅ **완료**)
   - [x] `/healthz` 로그 노이즈 제거 (`middleware.py` 적용) (✅ **완료**)
   > 📖 학습 노트: `docs_study/learning_step3_kubernetes_probes.md`

2. **자원 할당과 자동 확장 (Limits & HPA)**
   - [x] `hpa.yaml` 및 `values.yaml` 리소스 임계치 리뷰 완료 (✅ **완료**)
   - [x] CPU Throttling 및 스케일링 정책(Stabilization) 이해 (✅ **완료**)

## 🟠 4단계: 데이터베이스 생존기 및 폭주 제어 — 진행 중
1. **커넥션 풀(Connection Pool)의 한계와 PgBouncer**
   - [x] **이론:** Worker/Pod 증가 시 SQLAlchemy Pool도 함께 증가하는 구조 이해 (✅ **완료**)
   - [x] **부하 테스트:** `hey`로 `/health_check` 동시 요청 부하를 걸고 latency 증가 관측 (✅ **완료**)
   - [x] **PgBouncer 개념:** PgBouncer는 코드 옵션이 아니라 PostgreSQL 앞단의 커넥션 프록시이며, `prepared_statement_cache_size=0`은 PgBouncer 호환 준비 설정임을 정리 (✅ **완료**)
   - [ ] **선택 실습:** Supabase Pooler/PgBouncer 연결 URL로 교체 후 직접 연결 방식과 비교
   > 📖 학습 노트: `docs_study/learning_step4_database_resilience.md`
2. **외부 API 방어막 (Circuit Breaker) & 시맨틱 캐싱 (비용 최적화)**
   - [x] **Retry 유틸리티:** 외부 HTTP 호출용 `retry_async()` 및 `RetryExhaustedError` 작성 (✅ **진행 완료**)
   - [x] **EmbeddingClient 분리:** Hugging Face 임베딩 호출을 별도 client로 분리 (✅ **진행 완료**)
   - [x] **In-memory 임베딩 캐시:** Redis 도입 전 학습용 TTL cache로 임베딩 벡터 재사용 구조 적용 (✅ **진행 완료**)
   - [ ] **Circuit Breaker:** Hugging Face 임베딩 서버 반복 장애 시 빠른 실패 처리
   - [ ] **Provider Fallback:** 키워드 추출/최종 답변 생성 시작 전 provider 우회 정책 설계
   - [ ] **Redis Semantic Cache:** 분산 환경에서도 공유 가능한 캐시 저장소로 확장
   > 📖 학습 노트: `docs_study/learning_step4_2_external_api_resilience.md`

## ✅ 5단계: 관측성 (Observability) — 완료
LLM 애플리케이션은 일반 API 서버보다 장애 원인을 찾기 어렵습니다. 사용자의 질문이 들어온 뒤, 키워드 추출, 임베딩 서버 호출, Supabase RAG 검색, 최종 LLM 생성까지 여러 외부 시스템을 거치기 때문입니다.
따라서 요청 단위 추적 ID와 LLM 실행 추적, 중앙 집중형 로그를 먼저 붙여 운영 중 병목과 실패 지점을 확인할 수 있는 기반을 마련했습니다.

1. **LLM Observability: LangSmith**
   - [x] `LANGCHAIN_TRACING_V2` 기반 LangChain LCEL 자동 트레이싱 적용 (✅ **완료**)
   - [x] `APP_ENV`, `LANGCHAIN_PROJECT`, `LANGCHAIN_TAGS` 기반 환경별 추적 구분 (✅ **완료**)
   - [x] 모델별 응답 지연, 토큰 사용량, 프롬프트 실행 흐름 확인 기반 마련 (✅ **완료**)
   > 📖 학습 노트: `docs_study/learning_step4_langsmith.md`

2. **Backend Observability: OpenTelemetry + Grafana**
   - [x] `backend/app/base/opentelemetry.py` 기반 OTLP 로그 전송 구조 적용 (✅ **완료**)
   - [x] FastAPI lifespan에서 `setup_opentelemetry()`, `shutdown_opentelemetry()` 연동 (✅ **완료**)
   - [x] `middleware.py`에서 요청별 `trace_id` 생성 및 응답 헤더 전파 (✅ **완료**)
   - [x] `contextvars` + `TraceIdFilter`로 비동기 요청 컨텍스트의 로그 추적성 확보 (✅ **완료**)
   > 📖 학습 노트: `docs_study/learning_step5-1_opentelemetry_grafana.md`
   > 📖 학습 노트: `docs_study/learning_step5-2_observability_advanced.md`

3. **관측성 고도화 백로그**
   - [ ] OpenTelemetry Trace/Metric까지 확장하여 로그뿐 아니라 요청 span, latency, error rate를 대시보드화
   - [ ] `/api/v1/chat/stream/advanced` 내부 단계별 span 분리: 키워드 추출, 임베딩 호출, Supabase 검색, 최종 LLM 생성
   - [ ] LangSmith run id와 백엔드 `trace_id`를 연결하여 장애 분석 시 양쪽 대시보드를 함께 추적
   - [ ] Grafana Dashboard / Alert Rule 구성: error rate, p95 latency, 외부 API 실패율, SSE 중단율

---

## 🔵 6단계: 엔터프라이즈 AI 시스템 아키텍처 (신규 ✨)

1. **헤비 태스크의 완벽한 분리 (Message Queue & Worker Node)**
   - **문제점:** 1분이 넘어가는 문서 요약 요청 시 FastAPI 메인 스레드가 블로킹되어 타임아웃 발생.
   - **실습:** `Celery`, `Redis Queues`, `RabbitMQ`를 도입하여 RAG 태스크를 워커 노드로 분리하고, FastAPI는 상태(Status) 알림만 수행하게 만들기.

2. **세션 영속화 및 컨텍스트 관리 (State Management)**
   - **문제점:** 현재 AI가 이전 채팅을 전혀 기억하지 못함. 서버(Pod)가 다중화되면 메모리에 세션 상태를 저장할 수 없음.
   - **실습:** `session_id` 기반으로 대화 로그를 `Redis` 혹은 `Supabase` 에 영속화. 나아가 `LangGraph`의 Checkpointer를 활용하여 멀티 에이전트 워크플로우 통제.

3. **RAG 성능의 정량 평가 파이프라인 (AI Evaluation)**
   - **문제점:** 답변의 품질을 눈대중으로 파악하고 있음. (할루시네이션, 정확도 등)
   - **실습:** `Ragas` 프레임워크나 LLM-as-a-judge 기법을 배포 파이프라인(CI/CD)에 붙여, 수치 데이터 기반으로 RAG 파이프라인 성능 자동 점검하기.
