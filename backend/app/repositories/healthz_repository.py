from supabase import Client

class HealthzRepository:
    def __init__(self, supabase: Client):
        self.supabase = supabase

    def health_check(self, schema:str, table:str):
        """요청 받은 '스미카'와 '테이블'의 데이터를 1건 조회 한다 -> health check"""
        resp = self.supabase.schema(schema).table(table).select("*").limit(1).execute()
        return resp.data    

