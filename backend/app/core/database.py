# database.py
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings
from app.base.logger import logger

# 모듈 임포트 시 딱 한 번만 생성 → 싱글톤
engine = None
session_factory = None

async def create_engine():
    """Async SQLAlchemy engine 생성"""
    logger.info("create Async Engine")
    global engine
    engine = create_async_engine(
        settings.database_url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_recycle=settings.db_pool_recycle,
        echo=settings.db_echo,
        # 👇👇👇 이 줄을 추가해야 PgBouncer와 충돌하지 않습니다! 👇👇👇
        connect_args={
            "prepared_statement_cache_size": 0, 
            "statement_cache_size": 0
        }
    )

    global session_factory
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def dispose_engine():
    """앱 종료 시 커넥션 풀 반납"""
    await engine.dispose()

async def get_db_session():
    async with session_factory() as session:
        yield session

async def get_db_schema_session(schema: str):
    async with session_factory() as session:
        await session.execute(text(f"SET search_path = {schema}"))
        yield session