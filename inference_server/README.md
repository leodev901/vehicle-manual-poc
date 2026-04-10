---
title: Inference Server
emoji: 🤖
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---


# Inference Server (Embedding Microservice) 🚀

이 디렉토리는 메인 로직(FastAPI 등)과 무거운 AI 모델 처리를 완전히 분리하기 위해 구성된 **추론 전용 마이크로서비스(Inference Microservice)**입니다.

## 🏛️ 아키텍처 다이어그램 및 목적
```mermaid
graph LR
    A[Client/Web Browser] --> |HTTP GET/POST| B(Main Web API :8009)
    B -->|S2S HTTP POST| C{Inference Server :8010}
    
    style C fill:#f9f,stroke:#333,stroke-width:2px
```

* **메모리 최적화**: 무거운 PyTorch 연산과 모델(2GB 이상)을 메인 서버에서 분리하여 메인 서버의 무한 Scale-out이 가능해졌습니다.
* **보안성(CORS 불필요)**: 프론트엔드가 이 서버를 직접 호출하지 않습니다. 오직 백엔드 간의 **S2S(Server-to-Server) 통신**으로만 동작하기 때문에 CORS 설정이 불필요하며 외부 공격으로부터 안전합니다.

## 📦 Hugging Face Spaces (무료 클라우드) 배포 가이드

자체적으로 RAM 16GB를 제공하는 Hugging Face Spaces의 Docker 컨테이너 런타임에 **무료 배포**하는 방법입니다.

### 1단계: Hugging Face 가입 및 Space 생성
1. [Hugging Face 사이트](https://huggingface.co/)에 가입 및 로그인합니다.
2. 우측 상단 프로필 클릭 후 **"New Space"** 를 선택합니다.
3. 설정값을 다음과 같이 입력합니다:
   * **Space name**: `vehicle-manual-inference` (원하는 이름 기입)
   * **License**: `mit` (권장)
   * **Select the Space SDK**: `Docker` 클릭 ➡️ `Blank` 선택
   * **Space hardware**: `Free` (CPU basic · 16GB RAM · 2 vCPU)
   * **Public / Private**: `Private` (개인 프로젝트용 보안 권장)
4. **"Create Space"** 버튼을 클릭합니다.

### 2단계: 코드 업로드 (수동 방식 기준)
명령어(Git CLI)로 올리거나, 가장 편한 웹 브라우저 방식으로 올릴 수 있습니다.

**[빠른 웹 브라우저 방식]**
1. 생성된 Space 화면에서 **Add file** 버튼 ➡️ `Upload files` 를 클릭합니다.
2. 현재 PC의 `inference_server/` 폴더 안에 있는 아래 **3개의 파일**만 드래그 앤 드롭으로 업로드합니다:
   * `main.py`
   * `requirements.txt`
   * `Dockerfile` 
3. **Commit changes** 를 누르면 끝입니다!

### 3단계: 배포 확인 및 통신 적용
1. 코드가 올라가면 허깅페이스가 자동으로 `Dockerfile`을 읽고 서버를 빌드합니다. (약 3~5분 소요, `Building...` 상태 확인)
2. 초록색 `Running` 마크가 뜨면 성공입니다.
3. **App 탭** 우측 상단의 `⋮` 메뉴를 눌러 **"Embed this Space"**를 누르면 나오는 `Direct URL` 이 실제 API 주소입니다.
> 🔗 **배포된 실제 주소 예시**: `https://{본인아이디}-vehicle-manual-inference.hf.space`

이제 메인 서버의 `chat_service.py` 코드 중 `http://localhost:8010/api/v1/embed` 부분을 **새로 받은 Direct URL + /api/v1/embed** 로 교체하기만 하면 모든 연동이 끝납니다! 🎉


Hugging Fasce에 배포 하기
```bash
git remote add spaces https://leodev901:hf_자신의토큰복붙@huggingface.co/spaces/leodev901/inference-server

git push spaces main
```
