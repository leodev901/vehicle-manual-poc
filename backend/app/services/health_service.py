from supabase import Client

class HealthCheckService:
    @staticmethod
    def health_check(supabse: Client, schem:str, table:str):
        """조회"""
        resp = supabse.schema(schem).table(table).select("*").limit(1).execute()
        return resp.data