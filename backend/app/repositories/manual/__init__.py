# app/repositories/manual/__init__.py

# 폴더 내부의 파일들(. 파일명)에서 클래스들을 들고 옵니다.
from .protocol import ManualRepositoryProtocol
from .supabase_repository import ManualSupabaseRepository
from .mock_repository import ManualMockRepository
from .sqlalchemy_repository import ManualSqlAlchemyRepository

# (옵션) 외부에서 import * 할 때 노출할 목록을 명시적으로 제한할 수 있습니다.
__all__ = [
    "ManualRepositoryProtocol",
    "ManualSupabaseRepository",
    "ManualMockRepository",
    "ManualSqlAlchemyRepository",
]
