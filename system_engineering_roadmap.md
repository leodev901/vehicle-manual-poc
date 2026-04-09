# 대용량 트래픽 처리를 위한 시스템 엔지니어링 로드맵 🚀

FastAPI 기반의 어플리케이션을 넘어서, 수만 명의 트래픽을 견디는 엔터프라이즈 시스템 엔지니어로 성장하기 위한 실전 실습형 로드맵입니다.

---

## 🟣 0단계: 고급 어플리케이션 아키텍처 (객체 지향의 꽃: Protocol / ABC)
인프라를 확장하기 전에, 코드가 어떤 DB나 외부 서비스로 교체되더라도 절대 무너지지 않는 "결합도 0%"의 상태를 만드는 파이썬 심화 설계 기법입니다. (이전에 약속했던 내용입니다!)

- [x] **비동기 의존성 주입 (Class-based DI)**: 테스트 용이성을 위한 `Depends()` 객체 주입 및 파라미터 결합도 제거 (✅ **완료**)
1. **추상화(Abstraction)와 다형성**
   - **실습:** Service가 `SupabaseRepository`를 직접 바라보지 않고, `DatabaseProtocol` 이라는 껍데기(인터페이스)만 바라보도록 의존성을 역전(DIP) 시켜보기.
   - **학습:** `abc.ABC`와 `typing.Protocol`의 차이 (명시적 상속 vs 덕 타이핑).
2. **테스트 주도 개발 (Testable Architecture)**
   - **실습:** 진짜 DB 연결 없이, `FakeRepository`를 1초 만에 만들어서 Service의 비즈니스 로직만 순수하게 단위 테스트(Unit Test) 돌려보기.

## 🟢 1단계: 어플리케이션 레벨의 최적화 (단일 서버 성능 쥐어짜기)
가장 먼저, 작성한 코드가 서버 성능을 100% 끌어내고 있는지 확인해야 합니다.

- [x] **비동기 이벤트 루프 최적화**: 동기 I/O 블로킹 제거 및 `ainvoke()` 적용 (✅ **완료**)
- [x] **실시간 스트리밍 (SSE)**: 사용자 UX 극대화를 위한 Chunk 실시간 `yield` 기술 적용 (✅ **완료**)
1. **Gunicorn과 Uvicorn의 조화 (Worker & Process)**
   - **실습:** CPU 코어가 4개일 때, 1개의 Uvicorn만 띄워보고, Gunicorn으로 5개의 워커(Worker)를 띄워 부하 테스트 비교.
   - **학습:** GIL(Global Interpreter Lock)과 멀티 프로세싱의 개념.
2. **동기(Sync)와 비동기(Async)의 치명적 차이**
   - **실습:** 비동기 함수 내부에 무거운 동기 연산을 넣었을 때의 병목 현상 실습.

## 🟡 2단계: 컨테이너와 패키징 (Docker)
1. **엔터프라이즈급 Dockerfile 작성법**
   - **학습:** Multi-stage 빌드 전략, Slim 이미지를 통한 컨테이너 경량화 및 보안 강화 (Rootless).
2. **다중 환경 연동 (Docker Compose)**
   - **실습:** 서버, Redis(캐시), 프론트엔드를 하나의 `docker-compose.yml`로 묶어서 클릭 한 번에 배포.

## 🟠 3단계: 인프라 오케스트레이션 (Kubernetes)
1. **상태 진단과 자가 치유 (Probes)**
   - **실습:** 우리가 만든 `/healthz` API를 쿠버네티스 생명주기에 연동.
2. **자원 할당과 자동 확장 (Limits & HPA)**
   - **실습:** 트래픽 폭주 시 서버 복제본이 10개로 자동 증식하는 과정 참관 및 파이썬 CPU Throttling 대응.

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
