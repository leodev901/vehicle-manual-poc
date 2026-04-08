from fastapi import Request
from supabase import Client

def get_supabase_client(request: Request) -> Client:
    """
    Request 객체에서 app.state에 저장된 supabase 클라이언트를 추출하여 반환합니다.
    """
    return request.app.state.supabase
 