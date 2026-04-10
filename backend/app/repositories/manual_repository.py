from supabase import AsyncClient
from fastapi import Depends
from app.core.dependencies import get_supabase_client
# from sentence_transformers import SentenceTransformer

# 임베딩 모델 로드 별도 inference_server 서버에 모델 기동
# embedding = SentenceTransformer('intfloat/multilingual-e5-large')


class ManualRepository:
    def __init__(
        self, 
        supabase: AsyncClient = Depends(get_supabase_client)
    ):
        self.supabase = supabase

    # 차량 브랜드 조회
    async def list_brands(self):
        response = await self.supabase.schema("vehicle_manual_rag").table("brands").select("*").execute()
        return response.data

    # 선택된 브랜드의 라인업 조회 
    async def list_lineups(self, brand_id:str):
        response = await self.supabase.schema("vehicle_manual_rag").table("lineups").select("*").eq("brand_id", brand_id).execute()
        return response.data

    # 선택된 라인업의 모댈 조회 
    async def list_models(self, lineup_id:str):
        response = await self.supabase.schema("vehicle_manual_rag").table("models").select("*").eq("lineup_id", lineup_id).execute()
        return response.data   

    # RAG 하이브리드 검색 함수 (조회용)
    async def search_manual_rag(self, model_id:str, query:str, query_vector:list[float], top_k: int=5):
        """
        하이브리드 검색 수행 함수 
        임베딩 모델은 별도 외부 inference_server에서 작업해서 받도록 정정함
        """
        # 1. 쿼리 임베딩
        # e5 모델은 검색어(Query) 앞에 반드시 "query: "를 붙여야 합니다.
        # query_prefix = f"query: {query}"
        # query_vector = embedding.encode(query_prefix).tolist()
        
        # 2. Supabase RPC 호출
        params = {
            "query_text": query,             # 키워드 검색용
            "query_embedding": query_vector, # 벡터 검색용
            "match_count": top_k,            # 몇 개 가져올지
            "filter_model": model_id,        # 차량 모델로 필터링 메타데이터 필터링
            "full_text_weight": 0.3,         # 키워드 가중치
            "semantic_weight": 0.7           # 벡터 가중치 (의미 검색 중시)
        }
        
        # RPC 함수 호출 (스키마 명시 불필요, 함수는 public에 열려있음)
        response = await self.supabase.rpc("hybrid_search", params).execute()
        return response.data

    
        
        