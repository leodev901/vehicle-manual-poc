import os
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer

# 07_parser_final.py 에서 파서 클래스 가져오기
from AdvancedManualParser import AdvancedManualParser

# ---------------------------------------------------------
# [설정] Supabase 연결 및 타겟 설정
# ---------------------------------------------------------
# 본인의 Supabase Project URL과 API Key를 입력하세요.
SUPABASE_URL = "https://bhxwivkmovmgptmuttbb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJoeHdpdmttb3ZtZ3B0bXV0dGJiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NDA1ODEzNCwiZXhwIjoyMDc5NjM0MTM0fQ.toXpX7fo1GWTGmhSGSWDdecI_akc6JqozDKegqtfkvE"

# 적재할 차량 모델명 (나중에 검색할 때 이 이름으로 필터링합니다)
TARGET_MODEL_NAME = "LX3HEV"

# PDF 파일 경로
PDF_PATH = "app/docs/LX3HEV_2026_ko_KR.pdf"

# ---------------------------------------------------------
# [초기화] 클라이언트 및 모델 로드
# ---------------------------------------------------------
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("⏳ 임베딩 모델(multilingual-e5-large) 로딩 중... (첫 실행 시 다운로드 오래 걸림)")
# e5-large 모델 (1024차원) 사용
model = SentenceTransformer('intfloat/multilingual-e5-large')
print("✅ 모델 로딩 완료!")



def generate_embedding_text(chunk):
    """
    e5 모델 성능 최적화를 위한 텍스트 전처리
    - 문서(Passage)를 임베딩할 때는 반드시 "passage: " 접두어를 붙여야 합니다.
    """
    content_str = " ".join(chunk['content'])
    table_str = "\n".join(chunk['tables']) if chunk['tables'] else ""
    
    # 제목 + 본문 + 표 내용을 합침
    full_text = f"passage: 제목: {chunk['heading']} 내용: {content_str} {table_str}"
    return full_text.strip()

def main():
    print(f"\n🚀 [{TARGET_MODEL_NAME}] 매뉴얼 데이터 적재 시작")
    
    # 1. PDF 파싱
    parser = AdvancedManualParser(PDF_PATH)
    chunks = parser.run()
    
    print(f"📦 파싱 완료: 총 {len(chunks)}개 청크를 Supabase로 업로드합니다.")
    
    batch_data = []
    
    for i, chunk in enumerate(chunks):
        # 2. 임베딩 텍스트 생성
        text_to_embed = generate_embedding_text(chunk)
        
        # 3. 벡터 생성 (list로 변환)
        vector = model.encode(text_to_embed).tolist()
        
        # 4. DB에 넣을 데이터 구조 (SQL 스키마와 일치해야 함)
        row = {
            "model_name": TARGET_MODEL_NAME,
            "heading": chunk["heading"],
            "content": " ".join(chunk["content"]), # 원본 텍스트
            "page_num": chunk["page"],
            "metadata": {"tables": chunk["tables"]},
            "embedding": vector # 1024차원 벡터
        }
        batch_data.append(row)
        
        # 5. 배치 업로드 (50개씩 끊어서 전송)
        if len(batch_data) >= 50:
            try:
                # [중요] 스키마 명시: vehicle_manual_rag
                supabase.schema("vehicle_manual_rag").table("vehicle_manual").insert(batch_data).execute()
                print(f" - {i+1} / {len(chunks)} 처리 완료...")
                batch_data = [] # 초기화
            except Exception as e:
                print(f"❌ 업로드 중 에러 발생: {e}")
                break

    # 남은 데이터 처리
    if batch_data:
        supabase.schema("vehicle_manual_rag").table("vehicle_manual").insert(batch_data).execute()
        
    print(f"\n✨ 모든 데이터 적재가 완료되었습니다! (Model: {TARGET_MODEL_NAME})")

if __name__ == "__main__":
    main()