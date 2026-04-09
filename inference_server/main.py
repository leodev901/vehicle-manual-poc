# inference_server/main.py (예시 가이드)
from fastapi import FastAPI
from sentence_transformers import SentenceTransformer
from pydantic import BaseModel

from contextlib import asynccontextmanager

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

class EmbedRequest(BaseModel):
    text: str

@app.post("/api/v1/embed")
async def create_embedding(req: EmbedRequest):
    # 텍스트를 받아 벡터로 치환 후 리턴
    # e5 모델은 검색어(Query) 앞에 반드시 "query: "를 붙여야 합니다.
    if EMBEDDING_MODEL_NAME == "intfloat/multilingual-e5-large":
        query_prefix = f"query: {req.text}"
    else:
        query_prefix = req.text
    vector = model.encode(query_prefix).tolist()
    return {"embedding": vector}


# 실행 방법
# cd inference_server
# uvicorn main:app --port 8010 --reload