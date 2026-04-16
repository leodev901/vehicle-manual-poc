# ======================================================
# Stage 1: Builder — 패키지 빌드 전용 스테이지
# ======================================================
FROM python:3.12-slim AS builder

# 빌드에 필요한 시스템 패키지 설치 (gcc 등 컴파일러)
# 이 레이어는 최종 이미지에 포함되지 않습니다!
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# requirements만 먼저 복사 (소스 변경 시 캐시 재활용)
COPY requirements.txt .

# pip 패키지를 /build/packages 폴더에 설치 (나중에 Runtime에 복사할 것)
RUN pip install --no-cache-dir --prefix=/build/packages -r requirements.txt


# ======================================================
# Stage 2: Runtime — 실제 운영 이미지 (가볍고 안전하게!)
# ======================================================
FROM python:3.12-slim AS runtime

# ── 보안 강화: 전용 비루트 사용자 생성 ──────────────────
# -r: 시스템 계정 (로그인 불가), -u 1001: UID 고정
RUN groupadd -r appgroup -g 1001 && \
    useradd -r -u 1001 -g appgroup -s /sbin/nologin appuser

# ── 운영 환경 필수 유틸리티 설치 ─────────────────────────
# curl: K8s Pod 내부 디버깅 및 헬스체크 수동 테스트용
# ca-certificates: HTTPS 통신을 위한 루트 인증서
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ── Stage 1에서 빌드된 패키지만 복사 ─────────────────────
# 컴파일러, 빌드 도구는 하나도 들어오지 않습니다!
COPY --from=builder /build/packages /usr/local

WORKDIR /app
ENV PYTHONPATH=/app

# ── 앱 소스 복사 ──────────────────────────────────────────
COPY gunicorn_conf.py /app/gunicorn_conf.py
COPY app/ /app/app/

# ── 파일 소유권을 앱 유저로 변경 ─────────────────────────
RUN chown -R appuser:appgroup /app

# ── 앱 유저로 전환 (이후 모든 명령은 비루트로 실행) ────────
USER appuser

EXPOSE 8080

CMD ["gunicorn", "-c", "gunicorn_conf.py", "app.main:app"]