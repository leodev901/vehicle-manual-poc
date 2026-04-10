from supabase import create_client, Client

# [설정] Supabase 연결 데이터
SUPABASE_URL = "https://bhxwivkmovmgptmuttbb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJoeHdpdmttb3ZtZ3B0bXV0dGJiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NDA1ODEzNCwiZXhwIjoyMDc5NjM0MTM0fQ.toXpX7fo1GWTGmhSGSWDdecI_akc6JqozDKegqtfkvE"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def register_vehicle_info():
    print("🚗 차량 마스터 정보 등록 시작...")
    
    # 1. 브랜드 등록 (기아)
    brand_data = {"brand_id": "KI", "brand_nm": "기아"}
    try:
        supabase.schema("vehicle_manual_rag").table("brands").upsert(brand_data).execute()
        print("✅ 브랜드(KI) 등록 완료")
    except Exception as e:
        print(f"이미 존재하거나 오류: {e}")

    # 2. 라인업 등록 (스포티지)
    lineup_data = {
        "lineup_id": "NQ5", 
        "lineup_nm": "스포티지", 
        "brand_id": "KI",
        "type": "SUV"
    }
    try:
        supabase.schema("vehicle_manual_rag").table("lineups").upsert(lineup_data).execute()
        print("✅ 라인업(NQ5) 등록 완료")
    except Exception as e:
        print(f"이미 존재하거나 오류: {e}")

    # 3. 모델 등록 (스포티지 하이브리드)
    model_data = {
        "model_id": "NQ5HEV",
        "model_nm": "스포티지 하이브리드 (2025)",
        "lineup_id": "NQ5",
        "gen_no": 5,
        "fuel_type": "HEV"
    }
    try:
        supabase.schema("vehicle_manual_rag").table("models").upsert(model_data).execute()
        print("✅ 모델(NQ5HEV) 등록 완료")
    except Exception as e:
        print(f"이미 존재하거나 오류: {e}")

    print("\n✨ 모든 마스터 정보가 준비되었습니다. 이제 임베딩 적재를 다시 실행하세요!")

if __name__ == "__main__":
    register_vehicle_info()
