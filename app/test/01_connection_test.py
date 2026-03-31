from pymilvus import connections, utility

print("Milvus 서버 연결 시도 중...")

# 1. Milvus 연결 (Docker로 띄운 서버에 접속)
try:
    connections.connect("default", host="localhost", port="19530")
    print("✅ Milvus 서버 연결 성공!")
    
    # 2. 연결 상태 확인 (현재 서버에 있는 컬렉션 리스트 조회)
    collections = utility.list_collections()
    print(f"현재 생성된 컬렉션 리스트: {collections}")
    
except Exception as e:
    print(f"❌ 연결 실패: {e}")