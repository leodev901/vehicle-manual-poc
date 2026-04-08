from fastapi import FastAPI
from app.api.routes import register_reoutes
from app.core.database import create_supabase_client

async def life_span(app: FastAPI) -> None:
    print("Starting up...")
    # supabase client를 생성해서 state에 저장합니다. 나중에 요청 별 state에서 요청을 꺼내 예정
    app.state.supabase = create_supabase_client()

    yield

    print("Shutting down...")



def create_app() -> FastAPI:
    app = FastAPI(
        title="Vehicle Manual RAG",
        version="0.1.0",
        description="...",
        lifespan=life_span
    )

    register_reoutes(app)

    return app


app = create_app()