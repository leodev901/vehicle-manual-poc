import time
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------
# [설정] 연결 정보
# ---------------------------------------------------------
SUPABASE_URL = "https://bhxwivkmovmgptmuttbb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJoeHdpdmttb3ZtZ3B0bXV0dGJiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQwNTgxMzQsImV4cCI6MjA3OTYzNDEzNH0.0RXj2Hw1OKsMjSeVO4mtYUR6pX35O7xqKWAL76lD5xs"
TARGET_MODEL_NAME = "LX3HEV" # 검색할 차량 모델

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("⏳ 검색용 임베딩 모델 로딩 중...")
model = SentenceTransformer('intfloat/multilingual-e5-large')
print("✅ 검색 시스템 준비 완료!\n")

def search_hybrid(user_query, top_k=3):
    """
    하이브리드 검색 수행 함수
    """
    # 1. 쿼리 임베딩
    # e5 모델은 검색어(Query) 앞에 반드시 "query: "를 붙여야 합니다.
    query_prefix = f"query: {user_query}"
    query_vector = model.encode(query_prefix).tolist()
    
    # 2. Supabase RPC 호출
    params = {
        "query_text": user_query,        # 키워드 검색용
        "query_embedding": query_vector, # 벡터 검색용
        "match_count": top_k,            # 몇 개 가져올지
        "filter_model": TARGET_MODEL_NAME, # 모델명 필터링
        "full_text_weight": 0.3,         # 키워드 가중치
        "semantic_weight": 0.7           # 벡터 가중치 (의미 검색 중시)
    }
    
    # RPC 함수 호출 (스키마 명시 불필요, 함수는 public에 열려있음)
    response = supabase.rpc("hybrid_search", params).execute()
    return response.data

def main():
    print("="*50)
    print(f"🚗 {TARGET_MODEL_NAME} 차량 매뉴얼 AI 검색기")
    print("사용법: 궁금한 점을 물어보세요. (종료하려면 'q' 또는 '종료' 입력)")
    print("="*50)
    
    while True:
        user_input = input("\n🗣️ 질문 입력: ").strip()
        
        if not user_input:
            continue
            
        if user_input.lower() in ['q', 'exit', 'quit', '종료', '그만']:
            print("👋 프로그램을 종료합니다.")
            break
            
        start_time = time.time()
        results = search_hybrid(user_input,5)
        end_time = time.time()
        
        print(f"\n🔍 검색 결과 ({len(results)}건, {end_time - start_time:.2f}초 소요):")
        
        if not results:
            print("❌ 검색 결과가 없습니다. 다른 질문을 해보세요.")
            continue
            
        for i, item in enumerate(results):
            print(f"\n[{i+1}위] 📄 {item['heading']} (p.{item['page_num']})")
            # 본문이 너무 길면 200자까지만 보여주기
            preview = item['content'][:500].replace("\n", " ") + "..."
            print(f"   내용: {preview}")

if __name__ == "__main__":
    main()