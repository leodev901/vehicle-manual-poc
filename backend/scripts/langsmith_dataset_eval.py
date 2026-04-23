"""
[실습 8-1] LangSmith Dataset & Evaluation 자동화

실행 방법:
  cd backend
  source .venv/bin/activate
  python scripts/langsmith_dataset_eval.py

확인 방법:
  https://smith.langchain.com → vehicle-manual-poc 프로젝트 → Experiments 탭
"""
import os
from dotenv import load_dotenv

load_dotenv()

from langsmith import Client
from langsmith.evaluation import evaluate
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# LangSmith 클라이언트 초기화
# LANGCHAIN_API_KEY 환경변수를 자동으로 사용합니다
client = Client()

DATASET_NAME = "vehicle-manual-qa-v1"


def create_dataset():
    """
    차량 매뉴얼 Q&A Dataset을 LangSmith에 생성합니다.

    Dataset은 테스트 케이스의 모음입니다.
    한 번 만들어두면 프롬프트나 모델이 바뀌어도 재사용할 수 있습니다.
    """
    # 이미 존재하는 데이터셋이면 재생성하지 않음
    existing = list(client.list_datasets(dataset_name=DATASET_NAME))
    if existing:
        print(f"✅ Dataset '{DATASET_NAME}' 이미 존재합니다. 재사용합니다.")
        return existing[0]

    # 테스트 케이스 정의: inputs(입력) + outputs(기대 정답)
    examples = [
        {
            "inputs": {"question": "에어백이 작동하지 않을 때 어떻게 해야 하나요?"},
            "outputs": {"answer": "에어백 경고등이 켜진 경우 즉시 공인 서비스센터를 방문하여 점검받아야 합니다."}
        },
        {
            "inputs": {"question": "타이어 공기압은 얼마로 유지해야 하나요?"},
            "outputs": {"answer": "일반적으로 앞/뒤 타이어 모두 32~35 PSI를 권장하며, 정확한 수치는 차량 도어 스티커에서 확인하세요."}
        },
        {
            "inputs": {"question": "엔진오일 교체 주기는 얼마인가요?"},
            "outputs": {"answer": "일반 엔진오일은 5,000~10,000km마다, 합성 엔진오일은 15,000km마다 교체를 권장합니다."}
        },
        {
            "inputs": {"question": "브레이크 패드가 마모되면 어떤 증상이 나타나나요?"},
            "outputs": {"answer": "금속성 마찰음, 제동 거리 증가, 페달 진동 등이 나타납니다. 즉시 교체가 필요합니다."}
        },
        {
            "inputs": {"question": "냉각수가 부족하면 어떻게 되나요?"},
            "outputs": {"answer": "엔진 과열(오버히트)이 발생할 수 있으며, 심하면 엔진 손상으로 이어질 수 있습니다."}
        },
    ]

    # LangSmith에 Dataset 업로드
    dataset = client.create_dataset(
        dataset_name=DATASET_NAME,
        description="차량 매뉴얼 RAG 챗봇 평가용 Q&A 데이터셋 (v1)"
    )

    client.create_examples(
        inputs=[e["inputs"] for e in examples],
        outputs=[e["outputs"] for e in examples],
        dataset_id=dataset.id
    )

    print(f"✅ Dataset '{DATASET_NAME}' 생성 완료! ({len(examples)}개 예시)")
    return dataset


def build_chain(model_name: str = "gpt-4o-mini"):
    """
    평가할 체인을 구성합니다.
    model_name을 바꾸면 다른 모델로 평가할 수 있습니다.
    """
    llm = ChatOpenAI(model=model_name, temperature=0)

    # 현재 프로젝트와 유사한 간소화된 RAG 프롬프트
    prompt = ChatPromptTemplate.from_template(
        """당신은 차량 매뉴얼 전문 어시스턴트입니다.
        
질문: {question}

정확하고 간결하게 2~3문장으로 답변하세요."""
    )
    parser = StrOutputParser()
    return prompt | llm | parser


def keyword_match_evaluator(run, example):
    """
    사용자 정의 평가 함수: 키워드 일치율로 품질 측정

    run.outputs    → 모델이 실제로 생성한 답변
    example.outputs → Dataset에 정의된 정답

    점수 기준:
    - 1.0 : 정답 핵심 키워드를 모두 포함
    - 0.5~ : 절반 이상 포함
    - 0.0~ : 거의 포함 안 함
    """
    generated = run.outputs.get("output", "")
    expected = example.outputs.get("answer", "")

    # 정답 문장을 단어로 분리 (2글자 이상만 키워드로 사용)
    key_words = [w for w in expected.split() if len(w) >= 2][:6]
    if not key_words:
        return {"score": 0, "comment": "정답 키워드 없음"}

    # 각 키워드가 생성된 답변에 포함되어 있는지 체크
    matches = sum(1 for w in key_words if w in generated)
    score = matches / len(key_words)

    return {
        "score": score,
        "comment": f"키워드 일치율: {score:.0%} ({matches}/{len(key_words)}개 일치)"
    }


def run_evaluation(experiment_name: str = "gpt4o-mini-baseline"):
    """
    Dataset의 모든 예시에 대해 체인을 실행하고 결과를 평가합니다.
    LangSmith Experiments 탭에서 실험별 점수를 확인할 수 있습니다.
    """
    chain = build_chain(model_name="gpt-4o-mini")

    print(f"\n🔬 평가 실행 중: {experiment_name}")
    print(f"   Dataset: {DATASET_NAME}")

    results = evaluate(
        # 평가할 체인: inputs를 받아 output을 반환하는 callable
        lambda inputs: chain.invoke(inputs),
        data=DATASET_NAME,
        evaluators=[keyword_match_evaluator],
        # experiment_prefix: LangSmith에서 실험 이름으로 표시됨
        experiment_prefix=experiment_name,
        metadata={
            "model": "gpt-4o-mini",
            "dataset_version": "v1",
            "description": "기본 프롬프트로 gpt-4o-mini 평가"
        }
    )

    print(f"\n✅ 평가 완료!")
    print(f"👉 LangSmith 대시보드 → Experiments 탭에서 '{experiment_name}' 결과를 확인하세요.")


if __name__ == "__main__":
    # 1단계: Dataset 생성 (이미 있으면 재사용)
    create_dataset()

    # 2단계: 평가 실행
    run_evaluation(experiment_name="gpt4o-mini-baseline")

    print("\n" + "="*60)
    print("📝 다음 실습: 프롬프트를 수정하고 같은 Dataset으로 재평가해보세요!")
    print("   experiment_name을 다르게 설정하면 결과를 비교할 수 있습니다.")
    print("="*60)
