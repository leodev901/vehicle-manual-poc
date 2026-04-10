from fastapi import FastAPI
from app.api.routes import register_routes
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import create_supabase_client
from app.core.llm import create_llm_client, create_langchain_client
from app.base.exceptions import register_exception_handlers
from app.base.middleware import RequestLoggingMiddleware


async def life_span(app: FastAPI) -> None:
    print("Starting up...")
    # supabase client를 생성해서 state에 저장합니다. 나중에 요청 별 state에서 요청을 꺼내 예정
    app.state.supabase = await create_supabase_client()
    app.state.llm = create_llm_client()
    app.state.langchain = create_langchain_client()

    yield

    print("Shutting down...")



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

    
    # CORS 미들웨어 추가 (프론트엔드 호출 허용)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], # 실무에서는 Vercel 도메인으로 특정하는 것이 안전합니다.
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # logging middleware 등록
    app.add_middleware(RequestLoggingMiddleware)
    


    return app


app = create_app()