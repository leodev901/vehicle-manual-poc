# 🐳 로드맵 2단계 (A): 엔터프라이즈급 Dockerfile — Multi-stage 빌드 & Rootless 보안

> 현재 `backend/dockerfile`을 기반으로, 실무 운영 환경에서 요구하는 수준의 컨테이너 최적화를 달성합니다.

---

## 1. 🔍 AS-IS: 현재 Dockerfile의 문제점

```dockerfile
# 현재 dockerfile (AS-IS)
FROM python:3.12-slim       # 1️⃣ slim이지만 여전히 무거운 빌드 도구가 포함됨

WORKDIR /app
ENV PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt   # 2️⃣ 빌드 산출물이 그대로 운영 이미지에 잔류

COPY gunicorn_conf.py /app/gunicorn_conf.py
COPY app/ /app/app/

EXPOSE 8080
CMD ["gunicorn", "-c", "gunicorn_conf.py", "app.main:app"]
# 3️⃣ root 권한으로 실행 중! (보안 취약)
```

### 문제 1: 이미지 크기
`pip install` 과정에서 컴파일러(`gcc`), 빌드 헤더 파일, 캐시 등이 이미지에 남습니다.
`--no-cache-dir`로 pip 캐시는 지우지만, **빌드에 사용된 시스템 라이브러리는 그대로 남습니다.**

### 문제 2: 보안 취약 (root 실행)
현재 컨테이너 안의 프로세스는 **root (UID 0)** 권한으로 실행됩니다.
```
# 컨테이너 내부에서 확인하면
$ whoami
root     ← 위험!
```

만약 앱에 취약점이 있어서 컨테이너가 해킹되면:
```
해커가 컨테이너 내부에 접근 성공
    │
    ▼
whoami → root → /etc/passwd 수정, 패키지 설치, 파일 시스템 마음대로 조작
    │
    ▼ (최악의 경우)
Docker socket 마운트라도 되어있으면 → Host 서버까지 탈출 가능! 💀
```

이 두 가지를 **Multi-stage 빌드**와 **Rootless 컨테이너** 기법으로 한 번에 해결합니다.

---

## 2. 🏗️ Multi-stage 빌드란?

```
단일 스테이지 빌드 (AS-IS)      멀티 스테이지 빌드 (TO-BE)

┌──────────────────────┐         ┌─────────────────────┐
│ python:3.12-slim     │         │ Stage 1: Builder    │  ← 빌드 전용 (무거워도 됨)
│                      │         │ python:3.12-slim    │
│ ✗ gcc, 빌드도구      │         │ pip install         │
│ ✗ 빌드 캐시           │    ──►  │ (빌드 산출물 생성)   │
│ ✓ 앱 소스            │         └──────────┬──────────┘
│ ✓ pip packages       │                    │ 완성된 패키지만
└──────────────────────┘                    ▼ 복사
     운영 이미지                  ┌──────────────────────┐
     크기: 약 500MB              │ Stage 2: Runtime     │  ← 운영 전용 (가벼워야 함)
                                 │ python:3.12-slim     │
                                 │ ✗ gcc, 빌드도구       │  ← 아예 없음!
                                 │ ✓ 앱 소스만           │
                                 │ ✓ pip packages만      │
                                 └──────────────────────┘
                                      운영 이미지
                                      크기: 약 250MB
```

**핵심:** 최종 이미지에는 **"앱 실행에 필요한 것만"** 담깁니다. 빌드 과정에서 쓴 도구들은 사라집니다.

---

## 3. 🔒 Rootless 컨테이너란?

```
root 실행 (AS-IS)                  Rootless 실행 (TO-BE)

컨테이너 안: UID=0 (root)          컨테이너 안: UID=1001 (appuser)
    │                                  │
    ▼                                  ▼
파일 시스템 전체 쓰기 가능          자기 /app 폴더만 접근 가능
패키지 설치 가능                   패키지 설치 불가 (운영엔 불필요)
모든 포트 열기 가능                1024 이하 포트 열기 불가 (1024 이상만)
컨테이너 탈출 위험 ❌              탈출해도 nobody 권한 ✅
```

Kubernetes에서는 `SecurityContext`로 root 실행을 아예 차단하는 정책을 적용하는 환경도 있습니다.
Rootless로 만들어두면 이런 정책 환경에서도 문제없이 배포됩니다.

---

## 4. 🛠️ TO-BE: 엔터프라이즈급 Dockerfile (샘플 코드)

```dockerfile
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
```

---

## 5. ⚖️ AS-IS vs TO-BE 비교

| 항목 | AS-IS (현재) | TO-BE (Multi-stage + Rootless) |
|---|---|---|
| **이미지 크기** | ~500MB | ~250MB (절반 수준) |
| **실행 권한** | root (UID 0) | appuser (UID 1001) |
| **빌드 도구 포함** | ✅ (gcc 등 잔류) | ❌ (완전 제거) |
| **K8s 보안 정책 호환** | ❌ (root 금지 정책 걸리면 배포 실패) | ✅ |
| **CI 빌드 시간** | 느림 (캐시 없으면 전체 재빌드) | 빠름 (레이어 캐시 최적화) |
| **보안 침해 시 피해 범위** | 호스트까지 탈출 가능성 | 컨테이너 내 /app만 접근 가능 |

---

## 6. 💡 레이어 캐시 최적화 전략

Dockerfile의 레이어는 **변경이 감지되면 그 아래 레이어를 모두 다시 실행**합니다.

```dockerfile
# ❌ 비효율적인 순서 (소스 코드 1줄 바꿔도 pip install 전체 재실행!)
COPY . .
RUN pip install -r requirements.txt

# ✅ 올바른 순서 (소스 코드만 바뀌면 pip 캐시 그대로 활용)
COPY requirements.txt .
RUN pip install -r requirements.txt   # ← 자주 변하지 않으므로 캐시됨
COPY . .                               # ← 자주 변하는 소스 코드는 마지막에
```

**캐시 활용 규칙:** 자주 변하지 않는 것 → 위쪽 / 자주 변하는 것 → 아래쪽

---

## 7. 🔑 핵심 요약

1. **Multi-stage 빌드** = "빌드 공장"과 "배송 상자"를 분리. 최종 이미지에는 운전에 필요한 것만.
2. **Rootless** = 컨테이너 안의 프로세스가 `appuser` 권한으로 실행. 해킹당해도 피해 최소화.
3. **레이어 캐시** = requirements.txt를 소스 코드보다 먼저 COPY해서 pip install 캐시 재활용.
4. **`--no-install-recommends`** = apt-get 시 권장 패키지 설치 안 함 → 이미지 추가 경량화.

---

## 8. 🗣️ Q&A 회고록

### Q1. runtime stage에 굳이 python:3.12-slim을 또 쓰나요? `FROM scratch`같은 걸 쓰면 더 작아지지 않나요?

**A.** Python 앱은 실행 시 Python 인터프리터가 반드시 필요합니다.  
`scratch`는 아무것도 없는 빈 이미지로, Go나 Rust처럼 단일 바이너리로 컴파일되는 언어에서 사용합니다.  
Python은 인터프리터 + 표준 라이브러리가 필요하므로 `python:3.12-slim`이 사실상 최소 기반입니다.  
더 줄이고 싶다면 `python:3.12-alpine`을 쓸 수 있지만 일부 C 확장 라이브러리(cryptography 등)가 호환 안 되는 경우가 있어서 실무에서는 `slim`이 더 안전합니다.
