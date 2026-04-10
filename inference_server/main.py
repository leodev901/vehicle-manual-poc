# inference_server/main.py (예시 가이드)
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from sentence_transformers import SentenceTransformer
from pydantic import BaseModel

from contextlib import asynccontextmanager

import logging

# 기본 로거 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# lifespan 구조를 활용해 서버가 켜질 때 딱 한 번만 2GB 모델 로드
model = None
EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-large"

@asynccontextmanager
async def life_span(app: FastAPI):
    # 시작 시점
    print("⏳ 모델 로딩 시작...")
    global model
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    print("✅ 모델 로딩 완료!")
    yield
    # 종료 시점
    print("🛑 모델 언로드")
    

app = FastAPI(
    title="Inference Server: SentenceTransformer",
    lifespan=life_span
)


# 전역 이벤트 헨들러 등록 -> 로깅
@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    # AGENTS.md 규칙: 내부 로깅은 상세하게 에러 스택을 남기고
    logger.exception("추론 서버 내부 치명적 에러 발생: %s", str(exc))
    
    # 사용자/외부 API에는 정제된 메시지만 전달
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "http_status_code": 500,
            "message": "서버 내부에서 임베딩 생성 중 오류가 발생했습니다. 서버 로그를 확인해주세요 (https://huggingface.co/spaces/leodev901/inference-server)"
        }
    )

# 루트 접근시 Swagger-ui로 리디렉션
@app.get("/")
async def root():
    return RedirectResponse(url="/docs")


class EmbedRequest(BaseModel):
    text: str

@app.post("/api/v1/embed")
async def create_embedding(req: EmbedRequest):
    logger.info(f"임베딩 생성 요청: {req.text}")
    
    # 텍스트를 받아 벡터로 치환 후 리턴
    # e5 모델은 검색어(Query) 앞에 반드시 "query: "를 붙여야 합니다.
    if EMBEDDING_MODEL_NAME == "intfloat/multilingual-e5-large":
        query_prefix = f"query: {req.text}"
    else:
        query_prefix = req.text
    vector = model.encode(query_prefix).tolist()    
    # logger.info(f"임베딩 생성 완료: {vector}")
    return {"embedding": vector}


# 실행 방법
# cd inference_server
# uvicorn main:app --port 8010 --reload