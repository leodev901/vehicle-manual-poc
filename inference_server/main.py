from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool # 비동기 블로킹 방지용
from sentence_transformers import SentenceTransformer
from pydantic import BaseModel
from typing import Union, List

from contextlib import asynccontextmanager
import logging

# 기본 로거 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

model = None
EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-large"

@asynccontextmanager
async def life_span(app: FastAPI):
    print("⏳ 모델 로딩 시작...")
    global model
    # 모델 로딩은 서버 시작 시 1회만 발생하므로 동기로 두어도 무방합니다.
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    print("✅ 모델 로딩 완료!")
    yield
    print("🛑 모델 언로드")
    
app = FastAPI(
    title="Inference Server: SentenceTransformer",
    lifespan=life_span
)

# 1. CORS 미들웨어 추가 (Vercel 프론트엔드 호출 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 실무에서는 Vercel 도메인으로 특정하는 것이 안전합니다.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    logger.exception("추론 서버 내부 치명적 에러 발생: %s", str(exc))
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "http_status_code": 500,
            "message": "서버 내부에서 임베딩 생성 중 오류가 발생했습니다. 서버 로그를 확인해주세요."
        }
    )

@app.get("/")
async def root():
    return RedirectResponse(url="/docs")


# 3. 배치 처리 지원: 단일 문자열(str) 또는 문자열 리스트(List[str]) 모두 수용
class EmbedRequest(BaseModel):
    text: Union[str, List[str]]

@app.post("/api/v1/embed")
async def create_embedding(req: EmbedRequest):
    # 입력값이 단일 문자열이면 리스트로 통일하여 처리
    texts = [req.text] if isinstance(req.text, str) else req.text
    logger.info(f"임베딩 생성 요청 수: {len(texts)}건")
    
    # E5 모델 접두어 처리 로직 (리스트 내포 활용)
    if EMBEDDING_MODEL_NAME == "intfloat/multilingual-e5-large":
        processed_texts = [f"query: {t}" for t in texts]
    else:
        processed_texts = texts

    # 2. 이벤트 루프 블로킹 방지: 별도 스레드에서 무거운 추론 작업 실행
    # model.encode는 리스트를 받아 다수의 벡터를 한 번에 반환할 수 있습니다.
    embeddings = await run_in_threadpool(model.encode, processed_texts)
    
    vector_list = embeddings.tolist()
    
    # 단일 문자열이 들어왔을 때는 기존 스펙과 동일하게 1차원 배열만 리턴
    if isinstance(req.text, str):
        return {"embedding": vector_list[0]}
    
    # 리스트가 들어왔을 때는 2차원 배열(리스트의 리스트) 리턴
    return {"embeddings": vector_list}