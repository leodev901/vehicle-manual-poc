# 🐳 로드맵 2단계 (B): Docker Compose — 다중 컨테이너 오케스트레이션

> 여러 개의 컨테이너(백엔드, 프론트엔드, Redis 등)를 하나의 설정 파일로 관리하고, 유기적으로 연결하는 방법을 학습합니다.

---

## 1. 🤹 Docker Compose란?

단일 `docker build`와 `docker run`은 컨테이너가 많아질수록 관리하기가 매우 까다로워집니다.
**Docker Compose**는 YAML 파일을 사용해 여러 컨테이너의 실행 옵션, 네트워크, 볼륨 등을 한 번에 정의합니다.

```bash
# AS-IS: 수동으로 하나씩 실행
docker run -d --name redis redis:alpine
docker run -d --name backend --link redis:redis my-backend
docker run -d --name frontend --link backend:backend my-frontend

# TO-BE: Compose 하나로 해결
docker-compose up -d
```

---

## 2. 🕸️ 컨테이너 간 네트워킹 (Service Discovery)

Docker Compose 안에서는 컨테이너끼리 IP 주소가 아닌 **'서비스 이름(Service Name)'**으로 통신할 수 있습니다.

```yaml
services:
  backend:
    ...
  redis:
    image: redis:alpine
```

- **백엔드에서 Redis에 접속할 때**: `localhost:6379`가 아닌 `redis:6379`로 접속 가능합니다.
- Docker가 내부 DNS 서버를 통해 `redis`라는 이름을 해당 컨테이너의 내부 IP로 맵핑해줍니다.

---

## 3. ⚖️ 인퍼런스 서버(Inference Server) 제외 이유

로드맵 실습에서는 인퍼런스 서버를 `docker-compose` 구성에서 제외했습니다.

- **이유**: 로컬 PC(특히 MacBook Pro가 아닌 환경이나 일반 PC)에서 무거운 Embedding 모델(torch 기반)을 컨테이너로 띄우면 CPU/Memory 점유율이 60~80% 이상 치솟아 원활한 개발이 불가능해집니다.
- **해결책**: 무거운 연산은 이미 배포된 **외부 Hugging Face API 서버**를 그대로 바라보게 설정하여 로컬 리소스를 절약합니다.

---

## 4. 🔗 프론트엔드와 백엔드의 연결 (CORS 주의사항)

```yaml
frontend:
  environment:
    - NEXT_PUBLIC_API_URL=http://localhost:8080
```

- **중요**: 프론트엔드(Next.js)가 브라우저에서 실행될 때는 컨테이너 내부 네트워크가 아닌 **사용자의 브라우저**에서 백엔드로 요청을 보냅니다.
- 따라서 `http://backend:8080`이 아니라, 호스트 PC에서 접근 가능한 `http://localhost:8080`을 엔드포인트로 설정해야 합니다.

---

## 5. 🏗️ 마이크로서비스 확장을 위한 준비: Redis

현재는 Redis를 사용하고 있지 않지만, 구성에 미리 포함한 이유는 **4~6단계의 엔터프라이즈 아키텍처** 때문입니다.

1. **세션 공유**: Pod가 여러 개로 늘어나면(HPA), 메모리 기반 세션은 유실됩니다. 이를 Redis에 저장하여 공유합니다.
2. **속도 최적화(Caching)**: 동일한 문서에 대한 중복 임베딩 연산을 피하기 위해 결과를 Redis에 캐싱합니다.

---

## 6. 🚀 실행 가이드 (나중에 맥북 서버에서 실행 시)

```bash
# 1. 빌드 및 백그라운드 실행
docker-compose up -d --build

# 2. 실행 중인 컨테이너 상태 확인
docker-compose ps

# 3. 로그 확인
docker-compose logs -f backend

# 4. 서비스 정지 및 삭제
docker-compose down
```

---

## 7. 🗣️ Q&A 회고록

### Q1. K8s가 있는데 왜 Docker Compose를 배우나요?
**A.** K8s는 운영 환경을 위한 거대하고 복잡한 시스템입니다.  
개발자가 로컬에서 코드를 수정하고 바로 테스트하기에는 Docker Compose가 훨씬 가볍고 빠릅니다. **"로컬 개발은 Compose, 실제 운영은 K8s"**가 표준 워크플로우입니다.

### Q2. Redis를 맥북 프로 K8s에 설치한다면?
**A.** 그때는 `docker-compose.yml`이 아닌, `Helm Chart`나 `K8s YAML`을 사용합니다. 하지만 설정값(`REDIS_HOST`, `REDIS_PORT`)을 환경변수로 관리하는 원리는 동일합니다.
