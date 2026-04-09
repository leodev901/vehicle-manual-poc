from supabase import create_client, Client

from app.core.config import settings
from app.base.logger import logger

SUPABASE_URL = settings.SUPABASE_URL
SUPABASE_KEY = settings.SUPABASE_KEY

def create_supabase_client() -> Client:
    """Supabase client 생성"""
    logger.info("create Supabse client")
    return create_client(SUPABASE_URL, SUPABASE_KEY)




