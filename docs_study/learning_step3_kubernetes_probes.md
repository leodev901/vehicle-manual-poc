# 🔷 로드맵 3단계: 인프라 오케스트레이션 (Kubernetes) — Probes & 자가 치유

> 현재 `backend/helm/templates/deployment.yaml`의 `periodSeconds: 720` (12분!)을 실무 표준으로 최적화하고,
> K8s Probe의 동작 원리와 Gunicorn과의 상호작용을 이해합니다.

---

## 1. 🔍 AS-IS: 현재 설정의 치명적 문제

```yaml
# deployment.yaml (현재)
readinessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 720      # ← 12분에 한 번 확인!! 💀
                          # 이 말은 Pod가 죽어도 최대 12분 동안 K8s가 모른다는 뜻!
```

이 `periodSeconds: 720`은 **개발 편의용 설정**으로 보입니다. 운영 환경에서는 절대 이렇게 놔두면 안 됩니다.

> ⚠️ **실제 상황**: 서버 Worker가 죽으면, Gunicorn이 1~3초 내로 복구하더라도  
> K8s는 12분 뒤에야 해당 Pod의 상태 변화를 인지합니다.  
> 그리고 **새로 뜬 Pod로 트래픽을 보내는 Readiness 판단**도 12분에 한 번입니다.

---

## 2. 🩺 Probe의 종류와 역할

K8s에는 3가지 Probe가 있고, 각자의 역할이 명확히 다릅니다.

```
┌─────────────────────────────────────────────────────────────────────┐
│                           K8s Probe 3종                             │
├──────────────────┬──────────────────────────────────────────────────┤
│ startupProbe     │ "앱이 최초로 기동되었나요?"                       │
│                  │ - 무거운 앱의 초기 기동 시간을 기다려 줍니다.      │
│                  │ - 이게 성공하기 전까지 liveness/readiness 비활성화│
├──────────────────┼──────────────────────────────────────────────────┤
│ readinessProbe   │ "요청을 받을 준비가 되었나요?"                    │
│                  │ - 실패하면 Service 트래픽을 이 Pod로 보내지 않음  │
│                  │ - 성공하면 트래픽 복구 → 로드밸런싱 대상에 포함   │
├──────────────────┼──────────────────────────────────────────────────┤
│ livenessProbe    │ "앱이 살아있나요? (좀비 프로세스 아닌가요?)"       │
│                  │ - 실패하면 컨테이너를 강제 재시작                 │
│                  │ - K8s 수준의 자가 치유(Self-healing)              │
└──────────────────┴──────────────────────────────────────────────────┘
```

---

## 3. 🔄 Probe의 동작 흐름 (타임라인)

```
Pod 기동 시작
    │
    ▼ [initialDelaySeconds: 10초 대기]
    │   앱이 뜨는 동안 Probe 체크 안 함
    │
    ▼ [readinessProbe 첫 번째 체크]
    │   /healthz → 200 OK?
    │   ✅ 성공 → Service 트래픽 허용
    │   ❌ 실패 → 트래픽 차단 유지, periodSeconds 후 재시도
    │
    ▼ [periodSeconds: N초마다 반복 체크]
    │
    ▼ [livenessProbe 실패 감지]
        Pod 내부 프로세스 응답 없음
        → failureThreshold 횟수 실패
        → K8s가 컨테이너 강제 재시작!
```

---

## 4. ⚙️ 핵심 파라미터 설명

```yaml
readinessProbe:
  httpGet:
    path: /healthz        # 체크할 엔드포인트 (200 응답 시 성공)
    port: 8080
  initialDelaySeconds: 10 # Pod 기동 후 첫 체크까지 대기 시간 (앱 구동 시간 고려)
  periodSeconds: 10       # 몇 초마다 체크할 것인가
  timeoutSeconds: 3       # 응답 기다리는 최대 시간 (초과 시 실패 처리)
  failureThreshold: 3     # 몇 번 연속 실패 시 "Dead" 판정 (기본값 3)
  successThreshold: 1     # 몇 번 연속 성공 시 "Ready" 판정 (기본값 1)
```

---

## 5. ⚙️ Gunicorn과 K8s Probe의 2단 방어 구조

```
이벤트: Worker가 갑자기 죽음!

[1단 방어: Gunicorn] ← 발동 조건: Worker 프로세스 사망 감지 (ms 단위)
  Gunicorn Master → 즉시 새 Worker 생성
  복구 시간: 1~3초 (Worker 기동 시간)
  한계: 새 Worker 기동 중 1~3초는 요청 실패

                  [2단 방어: K8s livenessProbe] ← 발동 조건: periodSeconds마다
    Gunicorn 자체가 죽은 경우(예: OOM Kill)
    → livenessProbe가 /healthz 응답 없음 감지
    → failureThreshold 횟수 실패 후 컨테이너 재시작
    → 새 Pod가 준비되면 readinessProbe 통과 후 트래픽 허용

즉, Gunicorn = 빠른 응급처치 (1~3초)
    K8s Probe = 최후의 보루 (느리지만 확실한 치유)
```

---

## 6. 🎯 TO-BE: 실무 표준 Probe 설정 (LLM 서비스 맞춤)

```yaml
readinessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 15  # LLM 모델 로딩 시간 고려 (너무 짧으면 재시작 루프)
  periodSeconds: 10         # 10초마다 체크 (720 → 10으로 대폭 단축!)
  timeoutSeconds: 5         # LLM 앱 특성상 응답이 살짝 느릴 수 있음
  failureThreshold: 3       # 3번 연속 실패(30초)가 되어야 트래픽 차단
  successThreshold: 1       # 한 번만 성공해도 즉시 트래픽 허용

livenessProbe:          # 추가! 현재 없는 상태 → 좀비 프로세스 방어
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 30   # readiness보다 늦게 시작 (앱 충분히 뜬 후 판단)
  periodSeconds: 30          # 너무 자주 하면 재시작 폭풍 발생 가능
  timeoutSeconds: 5
  failureThreshold: 3        # 3번 연속 실패(90초)가 되어야 컨테이너 재시작
```

---

## 7. 📊 periodSeconds 기준 비교

| 서비스 유형 | 권장 periodSeconds | 이유 |
|---|---|---|
| 일반 REST API | 5~10초 | 응답 빠름, 빠른 감지 필요 |
| **LLM 서비스 (우리)** | **10~30초** | LLM 처리 중 `/healthz`도 느릴 수 있음 |
| DB / 무거운 백엔드 | 30~60초 | 잦은 Probe로 인한 부하 방지 |
| 개발 환경 (편의용) | 720초 (현재) | 빠른 개발 사이클을 위해... (운영 절대 금지!) |

---

## 8. 🗣️ Q&A 회고록

### Q1. livenessProbe가 없어도 지금까지 잘 운영되지 않았나요?
**A.** 네, 짧은 시간 동안은 문제 없습니다. 하지만 Gunicorn Worker가 **"응답은 하지만 요청을 정상 처리하지 못하는 좀비 상태"**가 되거나, **메모리 누수로 결국 멈추는 상황**에서 livenessProbe가 없으면 K8s가 이를 영원히 모릅니다. `max_requests = 500`처럼 주기적인 Worker 재시작을 설정해뒀다면 어느 정도 방어되지만, 안전한 운영을 위해 livenessProbe는 있어야 합니다.

### Q2. livenessProbe 실패 시 재시작되면 기존 처리 중인 SSE 스트리밍은 어떻게 되나요?
**A.** 해당 컨테이너가 강제 재시작되면 스트리밍은 도중에 끊깁니다. 그래서:
1. `failureThreshold: 3`처럼 높게 설정해서 일시적인 오류로 인한 불필요한 재시작을 방지합니다.
2. `gunicorn_conf.py`의 `graceful_timeout: 30`이 livenessProbe보다 먼저 작동하면 Gunicorn이 현재 요청을 마저 처리하고 종료합니다. (단, livenessProbe 실패 시 K8s가 강제 `SIGKILL`을 보내면 Graceful Shutdown 불가)

### Q3. Probe가 자주 호출되면 로그가 너무 많이 쌓이지 않나요?
**A.** 맞습니다. `periodSeconds: 30`이면 하루에 `/healthz` GET 로그가 2,880번 쌓입니다. 완전히 노이즈입니다.
해결책은 `middleware.py`의 `EXCLUDE_PATH`에 `/healthz`를 추가하는 것입니다.
요청 자체는 정상 처리되어 K8s Probe 기능에는 영향 없고, 로그만 건너뜁니다.

```python
# backend/app/base/middleware.py
EXCLUDE_PATH = [
    "/health",
    "/healthz",    # ← K8s Probe 로그 노이즈 제거
    "/docs",
    ...
]
```

---

## 9. 📌 최종 적용값 (우리 프로젝트 홈서버 기준)

```yaml
readinessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 15   # LLM 모델 로딩 시간 고려
  periodSeconds: 30          # 홈서버 부하 고려, 30초로 보수적 설정
  timeoutSeconds: 10         # LLM 특성상 응답 살짝 느릴 수 있음
  failureThreshold: 3        # 3번 연속(90초) 실패 시 트래픽 차단
  successThreshold: 1        # 1번 성공 시 즉시 트래픽 허용

livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 60    # readiness보다 늦게 시작 (충분히 뜬 후 판단)
  periodSeconds: 600         # 10분마다 체크 (Gunicorn이 1단 방어하므로 보수적 설정)
  timeoutSeconds: 10
  failureThreshold: 3        # 3번 연속(30분) 실패 시 컨테이너 재시작
```

> 💡 **설계 철학**: Gunicorn이 Worker 장애를 1~3초 내로 먼저 복구합니다.
> K8s livenessProbe는 Gunicorn 자체가 죽는 극단적 상황의 최후 보루이므로,
> 홈서버 환경에서는 재시작 폭풍 방지를 위해 극도로 보수적으로 설정합니다.

