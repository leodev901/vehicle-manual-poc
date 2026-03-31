import time
from pymilvus import connections, Collection
from sentence_transformers import SentenceTransformer

# 1. Milvus 연결
connections.connect("default", host="localhost", port="19530")

# 2. 기존 컬렉션 불러오기
collection_name = "vehicle_manual_v1"
collection = Collection(collection_name)

# 3. 임베딩 모델 로드 (HuggingFace의 무료 모델 사용)
# - 'all-mpnet-base-v2': 성능이 매우 우수하고 768차원 벡터를 생성하는 표준 모델입니다.
print("⏳ 임베딩 모델 로딩 중... (처음엔 다운로드 때문에 시간이 좀 걸려요)")
model = SentenceTransformer('all-mpnet-base-v2')
print("✅ 모델 로딩 완료!")

# ---------------------------------------------------------
# [Step 1] 샘플 데이터 준비 (PoC 자료 기반)
# ---------------------------------------------------------
# 실제로는 PDF를 파싱해서 만들어야 하지만, 지금은 하드코딩으로 실습합니다.
data = [
    {
        "subject": "배터리 경고문",
        "text": "배터리 과열 경고문이 계속 표시될 경우, 먼저 차량을 안전한 곳에 정차시킨 후 시동을 끄고 배터리 온도가 내려갈 때까지 대기하십시오."
    },
    {
        "subject": "배터리 경고문",
        "text": "경고문이 계속 표시된다면 운전을 삼가고 즉시 블루핸즈 등에서 전문가의 점검 및 정비를 받아야 합니다."
    },
    {
        "subject": "타이어 공기압",
        "text": "항상 지정된 타이어 공기압을 유지하십시오. 주행 중 불필요한 전장품을 사용하지 마십시오."
    },
    {
        "subject": "충전 방법",
        "text": "아이오닉5는 100% 충전되는 데에 완속 3시간, 급속 1시간 소요됩니다."
    },
    {
        "subject": "진흙 탈출",
        "text": "차 바퀴가 진흙에 빠졌을 때 기어를 D(주행)와 R(후진)로 번갈아 변속하면서 가속 페달을 부드럽게 밟으십시오."
    }
]

# 데이터를 리스트로 분리 (Milvus는 컬럼별 리스트 입력을 좋아합니다)
subjects = [d["subject"] for d in data]
texts = [d["text"] for d in data]

# ---------------------------------------------------------
# [Step 2] 임베딩 (Text -> Vector 변환)
# ---------------------------------------------------------
print("⏳ 텍스트를 벡터로 변환 중...")
vectors = model.encode(texts)
# 결과: vectors 변수 안에는 768개의 숫자로 된 리스트들이 들어갑니다.
print(f"✅ 변환 완료! (데이터 개수: {len(vectors)}, 벡터 차원: {len(vectors[0])})")

# ---------------------------------------------------------
# [Step 3] 데이터 적재 (Insert)
# ---------------------------------------------------------
# 스키마 순서: [subject, text, vector] (id는 자동생성이므로 제외)
entities = [
    subjects,
    texts,
    vectors
]

insert_result = collection.insert(entities)
print(f"📥 데이터 적재 요청 완료. (생성된 PK ID: {insert_result.primary_keys})")

# ---------------------------------------------------------
# [Step 4] Flush (데이터 영구 저장 및 동기화)
# ---------------------------------------------------------
# Milvus는 메모리에 먼저 데이터를 쌓기 때문에, 디스크(MinIO)에 쓰고 검색 가능하게 하려면 flush가 필수입니다.
collection.flush()
print(f"💾 Flush 완료. 현재 총 데이터 개수: {collection.num_entities}개")