"""
[실습 5-1] LangSmith 기본 트레이싱 테스트

실행 방법:
  cd backend
  source .venv/bin/activate
  python scripts/langsmith_basic_test.py

확인 방법:
  https://smith.langchain.com → vehicle-manual-poc 프로젝트 → Traces
"""
import asyncio
import os
from dotenv import load_dotenv

# .env 파일을 먼저 로드해야 LANGCHAIN_* 환경변수가 설정됨
load_dotenv()

# LangChain은 아래 환경변수들이 설정되어 있으면 자동으로 LangSmith에 Trace를 전송함
# (langsmith 패키지가 LangChain 내부에 통합되어 있기 때문)
print(f"LangSmith 트레이싱 활성화: {os.getenv('LANGCHAIN_TRACING_V2')}")
print(f"프로젝트: {os.getenv('LANGCHAIN_PROJECT')}")

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


async def run_basic_trace_test():
    """
    가장 기본적인 LangSmith 트레이싱 테스트

    이 스크립트를 실행하면 LangSmith 대시보드에 Trace가 자동 생성됩니다.
    별도의 코드 변경 없이 환경변수만으로 작동한다는 것을 체험합니다.
    """

    # ChatOpenAI 모델 생성 (temperature=0 → 일관된 결과)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # 간단한 프롬프트 구성
    prompt = ChatPromptTemplate.from_template(
        "다음 자동차 관련 질문에서 핵심 키워드 3개를 추출하세요. 키워드만 콤마로 구분하여 출력하세요.\n\n질문: {question}"
    )
    parser = StrOutputParser()

    # LCEL 체인 조립: 프롬프트 → LLM → 파서
    chain = prompt | llm | parser

    test_questions = [
        "겨울철 타이어 공기압은 어떻게 관리해야 하나요?",
        "엔진 경고등이 갑자기 켜졌을 때 어떻게 해야 하나요?",
        "에어백 센서 오류 코드가 발생했습니다.",
    ]

    print("\n" + "="*60)
    print("🔬 LangSmith 기본 트레이싱 테스트 시작")
    print("="*60)

    for q in test_questions:
        # ainvoke() 실행 시 LangSmith에 자동으로 Trace가 전송됨
        result = await chain.ainvoke({"question": q})
        print(f"\n질문: {q}")
        print(f"키워드: {result}")

    print("\n" + "="*60)
    print("✅ 테스트 완료!")
    print("👉 https://smith.langchain.com 에서 Trace를 확인하세요.")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(run_basic_trace_test())
