# 1. 경량화된 파이썬 3.10 베이스 이미지 사용 (용량 최적화)
FROM python:3.10-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. [엔터프라이즈 최적화] GPU가 없는 무료 환경이므로, 
# 3GB짜리 GPU용 파이토치 대신 200MB짜리 CPU 전용 파이토치를 강제 설치하여 이미지 통계를 극적으로 줄입니다.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# 4. 일반 라이브러리 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. [Spaces 필수 보안] Hugging Face Spaces는 Root 권한을 허용하지 않습니다.
# 모델 다운로드 시 Permission Denied 에러가 나지 않도록 캐시 폴더를 쓰기 권한이 있는 tmp로 지정합니다.
ENV XDG_CACHE_HOME=/tmp/.cache
ENV HF_HOME=/tmp/.cache/huggingface

# 6. 소스 코드 복사
COPY . .

# 7. [Spaces 필수 규격] Hugging Face Spaces의 기본 개방 포트는 무조건 7860 입니다.
EXPOSE 7860
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
