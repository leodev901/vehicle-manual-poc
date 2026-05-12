import os

# ============================================================
# Gunicorn 운영 설정
# 모든 값은 환경변수(ENV)에서 읽어옵니다.
# values.yaml -> configmap.yaml -> ENV -> gunicorn_conf.py
# ============================================================

# 1. Worker 수 설정 (CPU 코어 수 기반)
# CPU 256m이므로 Worker 2개는 경합 발생 → 1개만
# 단, Gunicorn을 써서 Worker 죽으면 즉시 재시작 안정성 확보!
workers = int(os.getenv("GUNICORN_WORKERS", "1"))

# 2. 워커 클래스: Uvicorn의 ASGI 비동기 워커 사용 (FastAPI와 호환)
worker_class = "uvicorn.workers.UvicornWorker"

# 3. Worker당 최대 처리 요청 수 (메모리 누수 방지)
# LLM 응답 시간 고려: 100 요청 처리 후 Worker 재시작
max_requests = 100
max_requests_jitter = 50  # 100~150회 랜덤 (부하 분산)

# 5. 타임아웃 설정 (LLM 응답 시간 고려)
# SSE 스트리밍을 위한 타임아웃 설정 (매우 중요!)
# LLM 스트리밍은 수십 초가 걸릴 수 있으므로 기본 30초보다 넉넉하게 설정합니다.
timeout = int(os.getenv("GUNICORN_TIMEOUT", "180"))  # 3분 (LLM 최대 응답 시간보다 충분히 길게)
keepalive = 5   # K8s 환경 2~5초 이하 권장 (K8s Service의 idle 연결 끊기 정책과 충돌 방지)


# 4. 서버 바인딩 (HOST:PORT)
host = os.getenv("APP_HOST", "0.0.0.0")
port = os.getenv("APP_PORT", "8080")
bind = f"{host}:{port}"

# 5. 로깅 설정
loglevel = os.getenv("APP_LOG_LEVEL", "info").lower()   # configmap에서 APP_LOG_LEVEL로 주입됨
accesslog = "-"  # 표준 출력으로 로그 출력 (K8s에서 확인 용이)
errorlog = "-"   # 표준 에러로 로그 출력

# 6. Graceful 종료 (Pod가 죽을 때 처리 중인 요청을 완료하고 죽음)
graceful_timeout = 30

# 7. 프로세스 이름 설정 (K8s에서 식별 용이)
proc_name = "vehicle-manual-poc-api"