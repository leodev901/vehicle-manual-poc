# 🔭 LangSmith 완전 정복 가이드

> **목표**: LangSmith 회원가입 → 프로젝트 연결 → 트레이싱 분석 → LLM 모델별 성능 비교 → Prompt 튜닝까지 단계별로 실습한다.

---

## 목차

1. [LangSmith란?](#1-langsmith란)
2. [동작 원리](#2-동작-원리)
3. [회원가입 & API Key 발급](#3-회원가입--api-key-발급)
4. [이 프로젝트에 연결하기](#4-이-프로젝트에-연결하기)
5. [기본 트레이싱 실습](#5-기본-트레이싱-실습)
6. [LangChain 체인 자동 트레이싱](#6-langchain-체인-자동-트레이싱)
7. [LLM 모델별 성능 비교 분석](#7-llm-모델별-성능-비교-분석)
8. [Dataset & Evaluation (평가 자동화)](#8-dataset--evaluation-평가-자동화)
9. [Prompt 버전 관리 (Prompt Hub)](#9-prompt-버전-관리-prompt-hub)
10. [실무 활용 패턴 정리](#10-실무-활용-패턴-정리)

---

## 1. LangSmith란?

LangSmith는 **LLM 애플리케이션의 블랙박스를 열어주는 관찰 도구(Observability Platform)** 입니다.

```
일반 웹 서버 → Datadog, Sentry 로 로그/에러를 모니터링
LLM 앱      → LangSmith 로 프롬프트/토큰/응답/지연시간을 모니터링
```

### 왜 필요한가?

LLM 앱은 일반 코드와 달리 **"왜 이 답이 나왔는지"** 를 추적하기가 매우 어렵습니다.

| 문제 상황 | LangSmith 없을 때 | LangSmith 있을 때 |
|-----------|------------------|------------------|
| 답변이 이상함 | 로그를 뒤지면서 추측 | 해당 Trace를 클릭 → 어떤 프롬프트가 들어갔는지 즉시 확인 |
| 비용이 너무 높음 | 집계가 어려움 | 토큰 사용량/비용을 Run 단위로 확인 |
| 어떤 모델이 더 나은가? | 수동으로 A/B 테스트 | 동일 입력에 대해 자동 비교 실험 |
| 프롬프트 수정이 효과가 있나? | 감에 의존 | 이전 버전과 수치 비교 |

### 핵심 개념 3가지

```
Trace  → 하나의 요청 전체 실행 흐름 (예: 사용자 질문 1개)
Run    → Trace 안의 개별 단계 (키워드 추출 체인, RAG 체인, LLM 호출 등)
Project → Trace들을 묶는 논리적 단위 (예: "vehicle-manual-poc")
```

---

## 2. 동작 원리

### 데이터 흐름

```
┌─────────────────────────────────────────────────────┐
│                  내 FastAPI 서버                      │
│                                                      │
│  사용자 질문                                          │
│     │                                                │
│     ▼                                                │
│  chat_stream()                                       │
│     │                                                │
│     ├── [키워드 추출 체인] ──────────────────────────┤
│     │        keyword_chain.ainvoke(...)              │
│     │                                                │
│     ├── [RAG 검색] ─────────────────────────────────┤
│     │        repo.search_manual_rag(...)             │
│     │                                                │
│     └── [최종 답변 체인] ───────────────────────────┤
│              rag_chain.astream(...)                  │
│                                                      │
│  ↓ 각 단계에서 LangSmith SDK가 자동으로 데이터를 수집  │
└──────────────────────┬──────────────────────────────┘
                       │  (비동기, 백그라운드 전송)
                       ▼
         ┌─────────────────────────┐
         │   LangSmith 서버 (클라우드) │
         │   app.smith.langchain.com │
         └─────────────────────────┘
                       │
                       ▼
         ┌─────────────────────────┐
         │   LangSmith 대시보드    │
         │   - Trace 목록          │
         │   - 토큰 사용량          │
         │   - 지연시간 분석        │
         └─────────────────────────┘
```

### 핵심 메커니즘: 환경변수로 자동 활성화

LangSmith의 가장 강력한 특징은 **코드를 거의 바꾸지 않아도 된다**는 것입니다.

```python
# 이 환경변수들만 설정하면
# LangChain 라이브러리가 내부적으로 LangSmith에 자동으로 데이터를 전송합니다
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "ls-..."
os.environ["LANGCHAIN_PROJECT"] = "vehicle-manual-poc"

# 기존 코드 그대로 실행
keyword_chain = MANUAL_KEYWORD_EXTRACTION_PROMPT | active_llm | output_parser
keywords = await keyword_chain.ainvoke({"question": request.message})
# ↑ 이것만 실행해도 LangSmith에 자동으로 Trace가 기록됩니다!
```

---

## 3. 회원가입 & API Key 발급

### Step 1: 회원가입

1. 브라우저에서 **https://smith.langchain.com** 접속
2. **"Sign Up"** 클릭
3. GitHub 계정으로 소셜 로그인 권장 (가장 빠름)
4. 이메일 인증 완료

### Step 2: API Key 발급

1. 로그인 후 우측 상단 프로필 아이콘 클릭
2. **"Settings"** → **"API Keys"** 탭 이동
3. **"+ Create API Key"** 클릭
4. 이름 입력 (예: `vehicle-manual-poc-local`)
5. **`ls-`** 로 시작하는 키 복사 → 절대 public에 노출 금지!

```
⚠️  API Key는 발급 직후에만 전체 내용을 볼 수 있습니다.
    반드시 바로 복사해서 .env 파일에 저장하세요.
```

### Step 3: Project 생성

1. 좌측 사이드바 **"Projects"** 클릭
2. **"+ New Project"** 클릭
3. 이름에 `vehicle-manual-poc` 입력
4. 생성 완료

---

## 4. 이 프로젝트에 연결하기

### Step 1: .env 파일에 LangSmith 설정 추가

`backend/.env` 파일 맨 아래에 아래 내용을 추가하세요:

```bash
# ================================
# LangSmith 설정
# ================================
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=ls-여기에_발급받은_키_붙여넣기
LANGCHAIN_PROJECT=vehicle-manual-poc
```

### Step 2: config.py에 설정값 추가

`backend/app/core/config.py`에 아래 필드를 추가합니다:

```python
# 기존 settings 클래스에 추가
class Settings(BaseSettings):
    # ... 기존 설정들 ...

    # LangSmith 설정 (선택적 - 없으면 트레이싱 비활성화)
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "vehicle-manual-poc"
```

### Step 3: main.py에 LangSmith 초기화 코드 추가

```python
# backend/app/main.py 상단에 추가
import os
from app.core.config import settings

# LangSmith 환경변수 설정
# LangChain은 환경변수를 읽어서 자동으로 트레이싱을 활성화합니다
if settings.LANGCHAIN_TRACING_V2:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGCHAIN_ENDPOINT
    os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT
```

### Step 4: 동작 확인

```bash
# 가상환경 활성화 상태에서
cd backend
source .venv/bin/activate

# 서버 실행
uvicorn app.main:app --reload --port 8000

# 다른 터미널에서 API 요청 테스트
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "에어백 작동 방법은?", "llm_config": {"provider": "OPENAI", "model": "gpt-4o-mini"}, "model_id": 1}'
```

→ 요청 후 **https://smith.langchain.com** 에서 `vehicle-manual-poc` 프로젝트로 이동하면 Trace가 기록됩니다.

---

## 5. 기본 트레이싱 실습

### 실습 5-1: @traceable 데코레이터로 수동 트레이싱

LangChain을 사용하지 않는 일반 함수도 추적하고 싶을 때 사용합니다.

```python
# backend/app/services/chat_service.py 에 적용 예시
from langsmith import traceable

class ChatService:
    
    # @traceable 데코레이터를 붙이면 이 함수의 입출력이 LangSmith에 기록됩니다
    @traceable(name="키워드_추출", run_type="chain")
    async def _extract_keywords(self, question: str, provider: str) -> str:
        """
        사용자 질문에서 검색 키워드를 추출합니다.
        run_type으로 이 함수가 어떤 종류의 작업인지 분류합니다:
        - "chain"  : 여러 단계로 이뤄진 파이프라인
        - "llm"    : LLM 직접 호출
        - "tool"   : 외부 도구 호출
        - "retriever": 벡터 검색
        """
        active_llm = self.langchain.get(provider)
        output_parser = StrOutputParser()
        keyword_chain = MANUAL_KEYWORD_EXTRACTION_PROMPT | active_llm | output_parser
        return await keyword_chain.ainvoke({"question": question})

    @traceable(name="RAG_벡터검색", run_type="retriever")
    async def _search_documents(self, keywords: str, model_id: int) -> list:
        """
        키워드로 벡터 DB에서 관련 문서를 검색합니다.
        """
        # ... 기존 search 로직 ...
        pass
```

### 실습 5-2: LangSmith Client로 직접 Trace 생성

더 세밀하게 제어하고 싶을 때 사용합니다.

```python
# 실습용 독립 스크립트: backend/scripts/langsmith_basic_test.py
import asyncio
from langsmith import Client
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

async def run_basic_trace_test():
    """
    가장 기본적인 LangSmith 트레이싱 테스트
    이 스크립트를 실행하면 LangSmith 대시보드에 Trace가 생성됩니다
    """
    
    # LangChain 모델 생성
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # 간단한 프롬프트 체인 구성
    prompt = ChatPromptTemplate.from_template(
        "다음 자동차 관련 질문에서 핵심 키워드 3개를 추출하세요: {question}"
    )
    parser = StrOutputParser()
    
    # LCEL 체인 조립
    chain = prompt | llm | parser
    
    # 실행 - 이 시점에 LangSmith에 자동으로 Trace가 전송됩니다
    result = await chain.ainvoke({
        "question": "겨울철 타이어 공기압은 어떻게 관리해야 하나요?"
    })
    
    print(f"추출된 키워드: {result}")
    print("✅ LangSmith 대시보드에서 Trace를 확인하세요!")

if __name__ == "__main__":
    asyncio.run(run_basic_trace_test())
```

실행 방법:
```bash
cd backend
python scripts/langsmith_basic_test.py
```

---

## 6. LangChain 체인 자동 트레이싱

현재 프로젝트의 `chat_stream()` 메서드는 이미 LangChain LCEL을 사용하고 있습니다.  
환경변수만 설정하면 **아래 모든 단계가 자동으로 LangSmith에 기록**됩니다.

```
chat_stream() 요청 하나의 Trace 구조:

Trace: chat_stream (전체 요청)
  ├── Run: keyword_chain       ← MANUAL_KEYWORD_EXTRACTION_PROMPT | llm | parser
  │     ├── Run: ChatPromptTemplate.format()
  │     ├── Run: ChatOpenAI.invoke()        ← 토큰수, 비용, 지연시간 기록
  │     └── Run: StrOutputParser.parse()
  │
  ├── Run: httpx.post()        ← 임베딩 서버 호출 (수동 추적 필요)
  │
  ├── Run: search_manual_rag   ← Supabase 벡터 검색 (수동 추적 필요)
  │
  └── Run: rag_chain           ← RAG_CHAT_PROMPT | llm | parser
        ├── Run: ChatPromptTemplate.format()
        ├── Run: ChatOpenAI.astream()       ← 스트리밍 토큰 기록
        └── Run: StrOutputParser.parse()
```

### LangSmith 대시보드에서 확인하는 것들

1. **Trace 목록** → 각 사용자 요청별 전체 실행 시간
2. **Run 상세** → 각 단계별로 어떤 프롬프트가 입력되었는지, 어떤 답이 나왔는지
3. **Token Usage** → 이번 요청에서 몇 토큰이 소비되었는지 (비용 추적)
4. **Latency** → 어느 단계에서 시간이 가장 많이 걸렸는지

---

## 7. LLM 모델별 성능 비교 분석

현재 이 프로젝트는 `OpenAI`와 `Gemini` 두 가지 LLM을 지원합니다.  
LangSmith에서 **같은 질문에 대해 두 모델을 비교**하는 실습입니다.

### 실습 7-1: 비교 실험 스크립트

```python
# backend/scripts/langsmith_model_compare.py
"""
OpenAI vs Gemini 모델 성능 비교 실습
같은 질문을 두 모델에 넣고 LangSmith에서 결과를 비교합니다.
"""
import asyncio
import time
from langsmith import Client
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

# 테스트할 질문 목록
TEST_QUESTIONS = [
    "에어백이 작동하지 않는 이유는 무엇인가요?",
    "겨울철 타이어 공기압 관리 방법을 알려주세요.",
    "엔진 경고등이 켜졌을 때 어떻게 해야 하나요?",
    "브레이크 패드 교체 시기는 언제인가요?",
]

# 비교할 모델 설정
MODELS = {
    "openai-gpt4o-mini": ChatOpenAI(model="gpt-4o-mini", temperature=0),
    "gemini-2.0-flash": ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0),
}

# 키워드 추출 프롬프트 (현재 프로젝트와 동일한 형식)
KEYWORD_PROMPT = ChatPromptTemplate.from_template(
    """당신은 차량 매뉴얼 검색 시스템의 키워드 추출 전문가입니다.
    
사용자 질문: {question}

이 질문에서 차량 매뉴얼 검색에 사용할 핵심 키워드 2~3개를 추출하세요.
키워드만 콤마로 구분하여 출력하세요."""
)

async def compare_models():
    """
    여러 모델로 동일한 질문을 실행하고 LangSmith에 결과를 기록합니다.
    LangSmith 대시보드에서 모델별 지연시간, 토큰수를 비교할 수 있습니다.
    """
    parser = StrOutputParser()
    results = []
    
    for question in TEST_QUESTIONS:
        print(f"\n질문: {question}")
        print("-" * 50)
        
        for model_name, model in MODELS.items():
            # 체인 구성 (모델명을 태그로 추가)
            chain = KEYWORD_PROMPT | model.with_config(
                # 이 태그가 LangSmith 대시보드에서 필터링에 사용됨
                tags=[model_name, "keyword-extraction"],
                # 이 메타데이터가 분석에 활용됨
                metadata={"model": model_name, "task": "keyword_extraction"}
            ) | parser
            
            start_time = time.time()
            
            result = await chain.ainvoke({"question": question})
            elapsed = time.time() - start_time
            
            print(f"  [{model_name}] 키워드: {result} ({elapsed:.2f}초)")
            results.append({
                "model": model_name,
                "question": question,
                "keywords": result,
                "latency": elapsed
            })
    
    # 결과 요약
    print("\n" + "="*60)
    print("📊 비교 결과 요약")
    print("="*60)
    
    for model_name in MODELS.keys():
        model_results = [r for r in results if r["model"] == model_name]
        avg_latency = sum(r["latency"] for r in model_results) / len(model_results)
        print(f"\n{model_name}")
        print(f"  평균 응답 시간: {avg_latency:.2f}초")
    
    print("\n✅ LangSmith 대시보드에서 상세 비교를 확인하세요!")
    print("   필터: Tags → 모델명으로 필터링")

if __name__ == "__main__":
    asyncio.run(compare_models())
```

실행:
```bash
python scripts/langsmith_model_compare.py
```

### 실습 7-2: LangSmith 대시보드에서 비교하기

1. **Projects → vehicle-manual-poc** 이동
2. 좌측 상단 **"Filter"** 클릭
3. **Tags** 필터에 `openai-gpt4o-mini` 또는 `gemini-2.0-flash` 입력
4. **"Compare"** 버튼으로 두 모델의 Trace를 나란히 비교

비교할 수 있는 지표:
- `Latency` (응답 시간)
- `Total Tokens` (토큰 사용량)
- `Cost` (비용 추정)
- 출력 품질 (눈으로 직접 비교)

---

## 8. Dataset & Evaluation (평가 자동화)

**핵심 아이디어**: 좋은 질문-정답 쌍들을 미리 만들어두고(`Dataset`),  
코드가 바뀔 때마다 자동으로 테스트해서 성능이 오르는지 내리는지 측정합니다.

### 실습 8-1: Dataset 생성

```python
# backend/scripts/langsmith_dataset_test.py
"""
LangSmith Dataset을 만들고 자동 평가를 실행하는 실습
"""
from langsmith import Client
from langsmith.evaluation import evaluate, LangChainStringEvaluator
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

client = Client()

def create_dataset():
    """
    차량 매뉴얼 Q&A Dataset을 LangSmith에 생성합니다.
    이 Dataset은 나중에 모델/프롬프트가 바뀌어도 재사용할 수 있습니다.
    """
    dataset_name = "vehicle-manual-qa-dataset"
    
    # 이미 존재하는 데이터셋인지 확인
    datasets = list(client.list_datasets(dataset_name=dataset_name))
    if datasets:
        print(f"데이터셋 '{dataset_name}' 이미 존재합니다. 재사용합니다.")
        return datasets[0]
    
    # Dataset 생성 (테스트 케이스 정의)
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
    ]
    
    # LangSmith에 Dataset 업로드
    dataset = client.create_dataset(
        dataset_name=dataset_name,
        description="차량 매뉴얼 RAG 챗봇 평가용 Q&A 데이터셋"
    )
    
    client.create_examples(
        inputs=[e["inputs"] for e in examples],
        outputs=[e["outputs"] for e in examples],
        dataset_id=dataset.id
    )
    
    print(f"✅ Dataset '{dataset_name}' 생성 완료! ({len(examples)}개 예시)")
    return dataset


def build_chain():
    """평가할 체인을 생성합니다."""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # 현재 프로젝트와 유사한 RAG 프롬프트 (간소화 버전)
    prompt = ChatPromptTemplate.from_template(
        """당신은 차량 매뉴얼 전문 어시스턴트입니다.
        
질문: {question}

정확하고 간결하게 답변하세요."""
    )
    parser = StrOutputParser()
    return prompt | llm | parser


def run_evaluation():
    """
    Dataset의 모든 예시에 대해 체인을 실행하고 결과를 평가합니다.
    """
    dataset_name = "vehicle-manual-qa-dataset"
    chain = build_chain()
    
    # 평가 함수 정의
    def answer_evaluator(run, example):
        """
        LLM의 답변과 정답을 비교하는 사용자 정의 평가 함수
        반환값: score (0~1), comment (평가 이유)
        """
        generated_answer = run.outputs.get("output", "")
        expected_answer = example.outputs.get("answer", "")
        
        # 간단한 키워드 일치 평가 (실제 프로젝트에서는 LLM 기반 평가 권장)
        # 정답의 핵심 단어가 모델 답변에 포함되어 있는지 확인
        key_words = expected_answer.split()[:5]  # 정답의 첫 5단어를 키워드로 사용
        matches = sum(1 for w in key_words if w in generated_answer)
        score = matches / len(key_words) if key_words else 0
        
        return {
            "score": score,
            "comment": f"키워드 일치율: {score:.0%}"
        }
    
    # 평가 실행
    results = evaluate(
        # 평가할 체인 (inputs를 받아 output을 반환하는 callable)
        lambda inputs: chain.invoke(inputs),
        data=dataset_name,
        evaluators=[answer_evaluator],
        experiment_prefix="vehicle-manual-gpt4o-mini",  # 실험 이름 접두사
        metadata={"model": "gpt-4o-mini", "version": "1.0"}
    )
    
    print(f"\n✅ 평가 완료!")
    print(f"   LangSmith 대시보드 → Experiments 탭에서 결과를 확인하세요.")


if __name__ == "__main__":
    create_dataset()
    run_evaluation()
```

실행:
```bash
python scripts/langsmith_dataset_test.py
```

### LangSmith 대시보드에서 결과 보기

1. **Projects → vehicle-manual-poc → Experiments** 탭
2. 실험 결과에서 각 테스트 케이스별 점수 확인
3. 프롬프트를 바꾼 후 다시 실행 → 점수 비교

---

## 9. Prompt 버전 관리 (Prompt Hub)

LangSmith의 **Prompt Hub**는 프롬프트를 코드에서 분리하여 관리하는 기능입니다.  
코드 배포 없이 프롬프트만 바꿀 수 있어 실무에서 매우 유용합니다.

### 현재 프로젝트 프롬프트 구조

```
backend/app/prompts/
└── chat_prompts.py
    ├── MANUAL_KEYWORD_EXTRACTION_PROMPT  ← 키워드 추출용
    └── RAG_CHAT_PROMPT                  ← 최종 답변 생성용
```

### 실습 9-1: 프롬프트를 Hub에 올리기

```python
# backend/scripts/langsmith_prompt_hub.py
"""
현재 프로젝트의 프롬프트를 LangSmith Hub에 업로드하는 실습
"""
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_core.messages import SystemMessage
from dotenv import load_dotenv

load_dotenv()

client = Client()

def push_keyword_extraction_prompt():
    """
    MANUAL_KEYWORD_EXTRACTION_PROMPT를 LangSmith Hub에 업로드합니다.
    한 번 올리면 버전이 자동으로 관리됩니다.
    """
    
    # 현재 프로젝트의 키워드 추출 프롬프트와 동일한 내용
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="""당신은 차량 매뉴얼 검색 시스템의 키워드 추출 전문가입니다.
사용자 질문을 분석하여 차량 매뉴얼에서 검색하기 좋은 핵심 키워드를 추출합니다.
출력 형식: 키워드1, 키워드2, 키워드3 (콤마로 구분, 3개 이내)"""),
        HumanMessagePromptTemplate.from_template("사용자 질문: {question}")
    ])
    
    # Hub에 업로드 (프롬프트명: vehicle-manual-keyword-extraction)
    url = client.push_prompt(
        "vehicle-manual-keyword-extraction",
        object=prompt,
    )
    print(f"✅ 프롬프트 업로드 완료: {url}")


def use_prompt_from_hub():
    """
    Hub에 저장된 프롬프트를 불러와서 체인에서 사용합니다.
    코드 변경 없이 Hub에서 프롬프트만 수정하면 됩니다!
    """
    from langchain import hub
    from langchain_openai import ChatOpenAI
    from langchain_core.output_parsers import StrOutputParser
    
    # Hub에서 최신 버전의 프롬프트 로드
    prompt = hub.pull("vehicle-manual-keyword-extraction")
    
    llm = ChatOpenAI(model="gpt-4o-mini")
    parser = StrOutputParser()
    
    chain = prompt | llm | parser
    result = chain.invoke({"question": "타이어 공기압 점검 방법"})
    
    print(f"키워드 추출 결과: {result}")


if __name__ == "__main__":
    push_keyword_extraction_prompt()
    use_prompt_from_hub()
```

실행:
```bash
python scripts/langsmith_prompt_hub.py
```

### Hub 활용 흐름

```
개발자: 프롬프트 v1 작성 → Hub에 push
         ↓
테스트: Dataset으로 평가 → 점수 60%
         ↓  
PM/기획자: Hub 대시보드에서 프롬프트 수정 (코드 수정 없이!)
         ↓
테스트: Dataset으로 평가 → 점수 75% (향상 확인)
         ↓
배포: 코드는 hub.pull()로 최신 버전 자동 사용
```

---

## 10. 실무 활용 패턴 정리

### 패턴 A: 에러 디버깅

사용자가 "이상한 답변을 받았다"고 신고했을 때:

```
1. LangSmith → Traces 목록
2. 시간 필터로 해당 시각 검색
3. Error 상태 필터 또는 error 태그 검색
4. 해당 Trace 클릭 → 어떤 프롬프트가 들어갔는지 확인
5. Run 상세에서 LLM 입출력 전체 확인
```

### 패턴 B: 비용 최적화

```
1. LangSmith → Projects → Metrics 탭
2. Token Usage 그래프로 일별 사용량 확인
3. 가장 토큰을 많이 쓰는 Run 유형 파악
4. 해당 프롬프트를 압축하거나 더 저렴한 모델로 교체
5. Experiments로 품질 저하 없는지 확인 후 배포
```

### 패턴 C: 지속적 품질 관리

```
개발 워크플로우에 통합:
1. CI/CD 파이프라인에 evaluate() 실행 추가
2. 점수가 기준 이하로 떨어지면 배포 차단
3. 프롬프트 실험은 항상 experiment_prefix로 이름 붙이기
4. 모델 업그레이드 전 Dataset으로 사전 검증
```

### 패턴 D: 이 프로젝트에 바로 적용할 수 있는 것들

| 활용 | 적용 위치 | 기대 효과 |
|------|-----------|-----------|
| Trace 자동 수집 | `main.py` 환경변수 설정 | 모든 API 요청의 LLM 호출 자동 기록 |
| 키워드 추출 품질 측정 | `chat_service.py` + Dataset | 모델별 키워드 품질 점수 비교 |
| OpenAI vs Gemini 비교 | 비교 스크립트 실행 | 비용/속도/품질 트레이드오프 파악 |
| RAG 검색 품질 측정 | `@traceable` 추가 | 어떤 문서가 얼마나 자주 검색되는지 |
| 프롬프트 A/B 테스트 | Prompt Hub + Experiments | 프롬프트 변경의 효과를 수치로 증명 |

---

## 빠른 시작 체크리스트

```
[ ] 1. https://smith.langchain.com 회원가입
[ ] 2. API Key 발급 (ls-... 로 시작)
[ ] 3. backend/.env 에 LANGCHAIN_* 환경변수 4개 추가
[ ] 4. backend/app/main.py 에 환경변수 초기화 코드 추가
[ ] 5. 서버 실행 후 API 1회 호출
[ ] 6. LangSmith 대시보드에서 Trace 확인
[ ] 7. (선택) 모델 비교 스크립트 실행
[ ] 8. (선택) Dataset 만들고 Evaluation 실행
[ ] 9. (선택) 프롬프트 Hub에 올리기
```

---

## 참고 링크

- 공식 문서: https://docs.smith.langchain.com
- Python SDK: https://github.com/langchain-ai/langsmith-sdk
- Evaluation 가이드: https://docs.smith.langchain.com/evaluation
- Prompt Hub: https://smith.langchain.com/hub
