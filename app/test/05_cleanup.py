from pymilvus import connections, utility, Collection

# 1. Milvus 연결
connections.connect("default", host="localhost", port="19530")

collection_name = "vehicle_manual_v1"

# 2. 컬렉션이 존재하는지 확인
if utility.has_collection(collection_name):
    collection = Collection(collection_name)
    
    # (중요) 메모리에 로드된 데이터 해제 (Release)
    # 이걸 해야 Milvus가 메모리(RAM)를 즉시 반환합니다.
    collection.release()
    print(f"📉 컬렉션 '{collection_name}' 메모리 해제 완료")

    # 3. 컬렉션 영구 삭제 (Drop)
    # 데이터베이스에서 테이블을 날리는 것과 같습니다. 실습 데이터가 모두 사라집니다.
    utility.drop_collection(collection_name)
    print(f"🗑️ 컬렉션 '{collection_name}' 영구 삭제 완료")
else:
    print(f"🤔 '{collection_name}' 컬렉션이 이미 없거나 삭제되었습니다.")

# 4. 연결 종료
connections.disconnect("default")
print("🔌 Milvus 서버 연결 종료")