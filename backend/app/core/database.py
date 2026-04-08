from app.core.config import settings
from supabase import create_client, Client

SUPABASE_URL = settings.SUPABASE_URL
SUPABASE_KEY = settings.SUPABASE_KEY

def create_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)




