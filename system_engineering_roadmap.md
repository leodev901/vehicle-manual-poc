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

## 🔴 4단계: 데이터베이스 생존기 및 폭주 제어
1. **커넥션 풀(Connection Pool)의 한계와 PgBouncer**
   - **실습:** 워커 증식으로 인한 DB 소켓 고갈(`Too many connections`) 재현 및 PgBouncer로 방어.
2. **외부 API 방어막 (Circuit Breaker) & 시맨틱 캐싱 (비용 최적화)**
   - **실습:** OpenAI 서버 장애 시 Gemini로 우회하는 서킷 브레이커 방어하기 및 `Tenacity` 재시도 파이프라인.
   - **실습:** `Redis`를 붙여서 똑같은 질문에 대해 LLM API를 안 치고 0.1초 만에 캐시에서 응답 반환하기.

## 🟤 5단계: 관측성 (Observability)
1. **분산 트레이싱 및 중앙 집중형 로깅**
   - **실습:** `OpenTelemetry`나 `Datadog`, `LangSmith`를 붙여서 텍스트 입력부터 최종 답변까지 마이크로 단위 병목 지점을 대시보드화.

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
