"""
[실습 7-1] OpenAI vs Gemini 모델 성능 비교

실행 방법:
  cd backend
  source .venv/bin/activate
  python scripts/langsmith_model_compare.py

확인 방법:
  https://smith.langchain.com → vehicle-manual-poc 프로젝트 → Traces
  필터: Tags → 모델명으로 필터링하여 비교
"""
import asyncio
import time
import os
from dotenv import load_dotenv

load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# --------------------------------------------------
# 테스트 데이터 정의
# --------------------------------------------------
TEST_QUESTIONS = [
    "에어백이 작동하지 않는 이유는 무엇인가요?",
    "겨울철 타이어 공기압 관리 방법을 알려주세요.",
    "엔진 경고등이 켜졌을 때 어떻게 해야 하나요?",
    "브레이크 패드 교체 시기는 언제인가요?",
]

# --------------------------------------------------
# 비교할 모델 정의
# 새로운 모델을 추가하려면 여기에 항목을 추가하세요
# --------------------------------------------------
MODELS = {
    "openai-gpt4o-mini": ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
    ),
    "gemini-2.0-flash": ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0,
    ),
}

# 키워드 추출 프롬프트 (현재 프로젝트와 동일한 형식 사용)
KEYWORD_PROMPT = ChatPromptTemplate.from_template(
    """당신은 차량 매뉴얼 검색 시스템의 키워드 추출 전문가입니다.

사용자 질문: {question}

이 질문에서 차량 매뉴얼 검색에 사용할 핵심 키워드 2~3개를 추출하세요.
키워드만 콤마로 구분하여 출력하세요."""
)


async def compare_models():
    """
    여러 모델로 동일한 질문을 실행하고 성능을 비교합니다.
    
    LangSmith 대시보드에서 아래 항목을 비교할 수 있습니다:
    - 응답 지연시간 (Latency)
    - 토큰 사용량 (Token Usage)
    - 비용 (Cost Estimate)
    - 출력 품질 (눈으로 직접 비교)
    """
    parser = StrOutputParser()
    results = []

    print("\n" + "="*60)
    print("🔬 OpenAI vs Gemini 모델 비교 실험 시작")
    print("="*60)

    for question in TEST_QUESTIONS:
        print(f"\n질문: {question}")
        print("-" * 50)

        for model_name, model in MODELS.items():
            # 모델에 태그와 메타데이터를 붙여서 LangSmith 필터링에 활용
            chain = KEYWORD_PROMPT | model.with_config(
                # tags → LangSmith 대시보드에서 필터링 가능
                tags=[model_name, "keyword-extraction", "model-comparison"],
                # metadata → 실험 분석에 활용
                metadata={
                    "model": model_name,
                    "task": "keyword_extraction",
                    "experiment": "openai-vs-gemini"
                }
            ) | parser

            start_time = time.time()

            try:
                result = await chain.ainvoke({"question": question})
                elapsed = time.time() - start_time
                print(f"  [{model_name}] 키워드: {result} ({elapsed:.2f}초)")
                results.append({
                    "model": model_name,
                    "question": question,
                    "keywords": result,
                    "latency": elapsed,
                    "error": None
                })
            except Exception as e:
                # 에러가 발생해도 다른 모델 테스트는 계속 진행
                elapsed = time.time() - start_time
                print(f"  [{model_name}] ❌ 오류 발생: {e}")
                results.append({
                    "model": model_name,
                    "question": question,
                    "keywords": None,
                    "latency": elapsed,
                    "error": str(e)
                })

    # --------------------------------------------------
    # 결과 요약 출력
    # --------------------------------------------------
    print("\n" + "="*60)
    print("📊 비교 결과 요약")
    print("="*60)

    for model_name in MODELS.keys():
        model_results = [r for r in results if r["model"] == model_name and r["error"] is None]
        if not model_results:
            print(f"\n{model_name}: 결과 없음 (모두 오류)")
            continue
        avg_latency = sum(r["latency"] for r in model_results) / len(model_results)
        print(f"\n{model_name}")
        print(f"  평균 응답 시간: {avg_latency:.2f}초")
        print(f"  성공률: {len(model_results)}/{len(TEST_QUESTIONS)}")

    print("\n" + "="*60)
    print("✅ 비교 실험 완료!")
    print("👉 LangSmith 대시보드에서 상세 비교를 확인하세요.")
    print("   Traces 탭 → Filter → Tags → 모델명으로 필터링")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(compare_models())
