from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility

# 1. Milvus 서버 연결
connections.connect("default", host="localhost", port="19530")

# ---------------------------------------------------------
# [Step 1] 스키마(뼈대) 정의 
# ---------------------------------------------------------
fields = [
    # 1. ID: 데이터의 고유 식별자 (자동으로 1, 2, 3... 번호표 배부)
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    # 2. Subject: 매뉴얼의 주제/제목 (검색 결과 보여줄 때 사용)
    FieldSchema(name="subject", dtype=DataType.VARCHAR, max_length=200),
    # 3. Text: 실제 매뉴얼 내용 본문
    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=2000),
    # 4. Vector: 본문 내용을 768개의 숫자로 변환한 임베딩 값
    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=768),
]

# 위 필드들을 모아서 스키마 완성
schema = CollectionSchema(fields=fields, description="차량 매뉴얼 검색용 DB")

# ---------------------------------------------------------
# [Step 2] 컬렉션(Collection) 생성
# ---------------------------------------------------------
collection_name = "vehicle_manual_v1"

# 만약 이미 같은 이름이 있으면 지우고 다시 만들기 (실습용 초기화)
if utility.has_collection(collection_name):
    utility.drop_collection(collection_name)
    print(f"🗑️ 기존 컬렉션 '{collection_name}' 삭제 완료")

# 컬렉션 생성 명령
collection = Collection(name=collection_name, schema=schema)
print(f"✨ 컬렉션 '{collection_name}' 생성 완료!")

# ---------------------------------------------------------
# [Step 3] 인덱스(Index) 생성 - 상황에 맞춰 골라 쓰세요!
# ---------------------------------------------------------

# [Option 1] FLAT: 가장 정확하지만 느림 (데이터가 적을 때 추천) [cite: 330, 331, 332]
# - 특징: 모든 데이터를 전수 조사. 정확도 100%.
# index_params = {
#     "metric_type": "COSINE",
#     "index_type": "FLAT",
#     "params": {}
# }

# [Option 2] IVF_FLAT: 속도와 정확도의 균형 (우리의 실습 선택) [cite: 333, 334, 335]
# - 특징: 데이터를 nlist 개의 클러스터로 나누어 검색. 가장 대중적.
index_params = {
    "metric_type": "COSINE",
    "index_type": "IVF_FLAT",
    "params": {"nlist": 128}  # nlist: 데이터를 128개 구역으로 나눔
}

# [Option 3] HNSW: 가장 빠르고 성능이 좋음 (메모리를 더 씀) [cite: 339, 340, 343]
# - 특징: 그래프(Graph) 기반 연결. 상용 서비스에서 가장 많이 씀 (To-Be 추천).
# - M: 그래프의 연결리스트 개수 (클수록 정확, 메모리 증가)
# - efConstruction: 인덱스 구축 시 탐색 깊이
# index_params = {
#     "metric_type": "COSINE",
#     "index_type": "HNSW",
#     "params": {"M": 16, "efConstruction": 64}
# }

# 선택된 인덱스 파라미터로 인덱스 생성
collection.create_index(field_name="vector", index_params=index_params)
print(f"🚀 {index_params['index_type']} 인덱스 생성 완료!")

# 최종 확인
print(f"\n[최종 상태] 생성된 컬렉션: {utility.list_collections()}")