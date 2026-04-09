from langchain_core.prompts import PromptTemplate, ChatPromptTemplate

# 프롬프트는 "비개발자(기획자, PM)"도 수정할 수 있어야 하기 때문에
# Service 코드 안에 프롬프트를 넣지 않고 분리합니다.
# → 분리하면 프롬프트만 독립적으로 버전 관리, A/B 테스트가 가능해집니다.

# 샘플 프롬프트 -> 차량 메뉴얼에서 미사용
KEYWORD_EXTRACTION_PROMPT = PromptTemplate.from_template("""
당신은 주어진 텍스트에서 핵심 키워드를 추출하는 전문가입니다.

[입력 텍스트]
{text}

[요구사항]
1. 텍스트의 핵심 내용을 가장 잘 나타내는 키워드 5~10개를 추출하세요.
2. 키워드는 명사 또는 명사구 형태로 작성하세요.
3. 키워드 간에는 쉼표(,)로 구분하세요.
4. 키워드는 한국어로 작성하세요.

[출력 형식]
키워드1, 키워드2, 키워드3, 키워드4, 키워드5, 키워드6, 키워드7, 키워드8, 키워드9, 키워드10
""")


MANUAL_KEYWORD_EXTRACTION_PROMPT = PromptTemplate.from_template("""
사용자는 차량 관련 질문을 합니다.
당신은 이 질문에서 차량 매뉴얼 RAG에서 검색할 키워드를 추출해야 합니다.

[사용자 질문]
{question}

[요구사항]
1. 질문의 핵심 내용을 가장 잘 나타내는 키워드 1개를 추출하세요.
2. 키워드는 명사 또는 명사구 형태로 작성하세요.
3. 키워드는 한국어로 작성하세요.

[출력 형식]
키워드1
""")



RAG_CHAT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", 
     "당신은 차량 매뉴얼을 안내하는 전문 AI 어시스턴트입니다.\n"
     "아래 검색된 매뉴얼 내용을 기반으로만 답변하세요.\n"
     "매뉴얼에 없는 내용은 '매뉴얼에서 확인되지 않는 내용입니다'라고 답변하세요."),
    ("system", "검색된 매뉴얼:\n{context}"),
    ("user", "{question}"),
])