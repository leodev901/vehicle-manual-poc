# 대용량 트래픽 처리를 위한 시스템 엔지니어링 로드맵 🚀

FastAPI 기반의 어플리케이션을 넘어서, 수만 명의 트래픽을 견디는 엔터프라이즈 시스템 엔지니어로 성장하기 위한 실전 실습형 로드맵입니다.

## 🟣 0단계: 고급 어플리케이션 아키텍처 (객체 지향의 꽃: Protocol / ABC)
인프라를 확장하기 전에, 코드가 어떤 DB나 외부 서비스로 교체되더라도 절대 무너지지 않는 "결합도 0%"의 상태를 만드는 파이썬 심화 설계 기법입니다. (이전에 약속했던 내용입니다!)

1. **추상화(Abstraction)와 다형성**
   - **실습:** Service가 `SupabaseRepository`를 직접 바라보지 않고, `DatabaseProtocol` 이라는 껍데기(인터페이스)만 바라보도록 의존성을 역전(DIP) 시켜보기.
   - **학습:** `abc.ABC`와 `typing.Protocol`의 차이 (명시적 상속 vs 덕 타이핑).
2. **테스트 주도 개발 (Testable Architecture)**
   - **실습:** 진짜 DB 연결 없이, `FakeRepository`를 1초 만에 만들어서 Service의 비즈니스 로직만 순수하게 단위 테스트(Unit Test) 돌려보기.

## 🟢 1단계: 어플리케이션 레벨의 최적화 (단일 서버 성능 쥐어짜기)
가장 먼저, 작성한 코드가 서버 성능을 100% 끌어내고 있는지 확인해야 합니다.

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
2. **외부 API 방어막 (Circuit Breaker)**
   - **실습:** LLM 서버 장애 시 우리 서버 스레드가 동반 자살하는 것 방어하기.

## 🟤 5단계: 관측성 (Observability)
1. **분산 트레이싱 및 중앙 집중형 로깅**
   - 요청의 시작점부터 DB 쿼리까지 병목 지점을 1분 안에 찾아내는 시스템 연동.
