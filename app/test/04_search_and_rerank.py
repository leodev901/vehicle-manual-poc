from pymilvus import connections, Collection
from sentence_transformers import SentenceTransformer, CrossEncoder

# 1. Milvus 연결
connections.connect("default", host="localhost", port="19530")

# 2. 컬렉션 로드 (매우 중요!)
# Milvus는 검색을 하려면 디스크에 있는 데이터를 메모리로 올려야 합니다.
collection = Collection("vehicle_manual_v1")
collection.load() 
print("✅ 컬렉션 메모리 로드 완료 (검색 준비 끝)")

# ---------------------------------------------------------
# [질문 준비]
# ---------------------------------------------------------
query = "배터리가 너무 뜨거운데 어떻게 해요?"
print(f"\n❓ 사용자 질문: {query}")

# ---------------------------------------------------------
# [Step 1] 1차 검색 (Retrieval) - IVF_FLAT 활용
# ---------------------------------------------------------
# 1-1. 질문을 벡터로 변환 (Bi-Encoder)
embed_model = SentenceTransformer('all-mpnet-base-v2')
query_vector = embed_model.encode([query])

# 1-2. 벡터 검색 실행
# * nprobe: 128개 구역(nlist) 중, 질문과 가장 가까운 '10개 구역'만 뒤져보라는 뜻 (속도 조절 핵심)
search_params = {
    "metric_type": "COSINE", 
    "params": {"nprobe": 10}
}

# 상위 3개만 가져오기 (Top-K)
results = collection.search(
    data=query_vector, 
    anns_field="vector", 
    param=search_params, 
    limit=3, 
    output_fields=["subject", "text"] # 결과에 포함할 필드
)

# 1차 검색 결과 저장
retrieved_docs = []
print("\n🔎 [1차 검색 결과] (Vector Similarity):")
for hits in results:
    for hit in hits:
        print(f" - [거리: {hit.distance:.4f}] {hit.entity.get('text')}")
        retrieved_docs.append(hit.entity.get('text'))

# ---------------------------------------------------------
# [Step 2] 재정렬 (Reranking) - Cross-Encoder 활용
# ---------------------------------------------------------
# 2-1. Reranker 모델 로드 (MS Marco 데이터로 학습된 모델 사용)
rerank_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

# 2-2. (질문, 답변) 쌍 만들기
pairs = [[query, doc] for doc in retrieved_docs]

# 2-3. 점수 계산 (얼마나 관련 있는지 0~10점 등으로 채점)
scores = rerank_model.predict(pairs)

# 2-4. 점수 높은 순서대로 정렬
ranked_results = sorted(zip(scores, retrieved_docs), key=lambda x: x[0], reverse=True)

print("\n🥇 [Reranking 결과] (Cross-Encoder):")
for score, doc in ranked_results:
    print(f" - [점수: {score:.4f}] {doc}")