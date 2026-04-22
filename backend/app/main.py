from fastapi import FastAPI
from app.api.routes import register_routes
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import create_engine, dispose_engine
from app.core.supabase import create_supabase_client
from app.core.llm import create_llm_clients, create_langchain_clients, create_chat_models
from app.base.exceptions import register_exception_handlers
from app.base.middleware import RequestLoggingMiddleware



# ============================================================
# uvloop: Python 기본 asyncio 이벤트 루프를 C 기반(libuv)으로 교체
# - Linux/macOS 환경에서 이벤트 루프 처리 속도 2~4배 향상
# - asyncio.create_task(), gather() 등 병렬 처리 시 특히 효과적
# - Windows 미지원 → 로컬 개발환경에서는 자동 skip
# - K8s 컨테이너(Linux)에서는 자동 적용됨
# ============================================================
import sys
import asyncio
if sys.platform != "win32":
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


async def life_span(app: FastAPI) -> None:
    print("Starting up...")
    # supabase client를 생성해서 state에 저장합니다. 나중에 요청 별 state에서 요청을 꺼내 예정
    app.state.supabase = await create_supabase_client()
    app.state.llm = create_llm_clients()
    app.state.langchain = create_langchain_clients()
    app.state.models = create_chat_models()
    
    # database engine 생성 - 싱글톤
    await create_engine()

    yield

    print("Shutting down...")
    # database engine 종료
    await dispose_engine()



def create_app() -> FastAPI:
    app = FastAPI(
        title="Vehicle Manual RAG",
        version="0.1.0",
        description="...",
        lifespan=life_span
    )

    # endpoint router 등록
    register_routes(app)

    # exception handelr 등록
    register_exception_handlers(app)

    # logging middleware 등록
    app.add_middleware(RequestLoggingMiddleware)
    
    # CORS 미들웨어 추가 (프론트엔드 호출 허용) - 가장 마지막에 추가
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], # 실무에서는 Vercel 도메인으로 특정하는 것이 안전합니다.
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app

# FastAPI 앱 생성
app = create_app()