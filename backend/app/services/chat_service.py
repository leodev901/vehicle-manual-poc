import json
from fastapi import Depends
from supabase import Client
from langchain_core.output_parsers import StrOutputParser

from app.core.dependencies import get_supabase_client, get_llm_client, get_langchain_client
from app.schemas.chat import ChatRequest
from app.prompts.chat_prompts import MANUAL_KEYWORD_EXTRACTION_PROMPT, RAG_CHAT_PROMPT, MOCK_CONTEXT


class ChatService:

    def __init__(
        self, 
        supabase: Client = Depends(get_supabase_client), 
        llm: dict = Depends(get_llm_client),
        langchain: dict = Depends(get_langchain_client),
    ):
        self.supabase = supabase
        self.llm = llm
        self.langchain = langchain
        

    async def chat(self, request: ChatRequest):

        #TODO: Kewyrod Extraction - LLM
        data = {}
        #TODO: session history 
        provider = request.llm_config.provider
        model = request.llm_config.model

        if provider.upper() == "OPENAI":
            client = self.llm[provider]
            response = client.responses.create(
                model=model,
                input=MANUAL_KEYWORD_EXTRACTION_PROMPT.format(
                    question=request.message
                )
            )
            keywords = response.output_text.strip()

        elif provider.upper() == "GEMINI":
            client = self.llm[provider]
            response = client.models.generate_content(
                model=model,
                contents=MANUAL_KEYWORD_EXTRACTION_PROMPT.format(
                    question=request.message
                )
            )
            keywords = response.text.strip()
        else:
            raise ValueError(f"{provider} provider를 지원하지 않습니다.")    

        # 키워드 결과 담기
        data["keywords"] = keywords 
        

        #TODO: RAG
        # 생략
        context = MOCK_CONTEXT
        

        #TODO: LLM (최종 답변 생성) - client는 앞선 client 사용
        # LangChain의 format_messages 반환값을 각 SDK에 맞는 형식으로 변환
        if provider.upper() == "OPENAI":
            # ChatPromptTemplate은 역할별 메시지 배열을 만들어줍니다
            messages = RAG_CHAT_PROMPT.format_messages(
                context=context,
                question=request.message
            )
            # OpenAI는 [{"role": "system", "content": "..."}, ...] 형식 사용
            openai_messages = [{"role": msg.type, "content": msg.content} for msg in messages]
            
            print(openai_messages)
            
            # 주의: system/human 등을 실제 OpenAI 롤(system/user 등)로 매핑 필요
            for msg in openai_messages:
                if msg["role"] == "human": msg["role"] = "user"
                
            final_response = client.chat.completions.create(
                model=model,
                messages=openai_messages
            )
            answer = final_response.choices[0].message.content.strip()
            
        elif provider.upper() == "GEMINI":
            # Gemini SDK(genai)의 generate_content는 content 인자로 텍스트나 배열을 받습니다
            # 시스템 프롬프트가 지원되지만, 단순성을 위해 프롬프트를 텍스트로 결합하여 전달 가능합니다
            combined_prompt = RAG_CHAT_PROMPT.format(
                context=context,
                question=request.message
            )
            print(combined_prompt)
            final_response = client.models.generate_content(
                model=model,
                contents=combined_prompt
            )
            answer = final_response.text.strip()
        
        # 답변 결과 답기 
        data["answer"] = answer

        #TODO: response

        return {
            "request": request,
            "response":data
        }
    
    async def chat_langchain(self,request: ChatRequest):
        """
        LangChain을 사용하여 Chat을 workflow를 수행합니다.
        """
        data = {}

        provider = request.llm_config.provider.lower() or "openai"
        
        # ==========================================
        # 1. 선택된 LangChain 모델 인스턴스 가져오기
        # ==========================================
        active_llm = self.langchain.get(provider)


        # ==========================================
        # 2. 출력 파서 생성 : LLM의 복잡한 응답 객체에서 최종 텍스트만 쏙 빼주는 역할
        # ==========================================
        # 모델이 반환하는 복잡한 응답 객체(AIMessage)에서 
        # 순수 텍스트(content)만 자동으로 추출해 주는 역할을 합니다.
        output_parser = StrOutputParser()

    
        # ==========================================
        # Step 1: 키워드 추출 체인 (LCEL)
        # ==========================================
        # prompt | llm | parser 순서로 흐르는 "파이프라인"을 조립합니다
        keyword_chain = MANUAL_KEYWORD_EXTRACTION_PROMPT | active_llm | output_parser
        print(f"keyword_chain: {keyword_chain}")

        # ==========================================
        # 체인 실행 (.invoke) -> 프롬프트 채우기, API 호출, 텍스트 파싱이 한방에 처리됨!
        # ==========================================
        # 프롬프트 템플릿에 들어갈 변수만 딕셔너리로 넘겨주면, 
        # 프롬프트 완성 -> 모델 호출 -> 텍스트 추출이 한 번에 처리됩니다.
        keywords = await keyword_chain.ainvoke({
            "question": request.message
        })
        # 키워드 추출 저장
        data["keywords"] = keywords

        #TODO: RAG 검색 (생략)
        context = MOCK_CONTEXT

        # ==========================================
        # Step 2: 최종 답변 생성 체인 (LCEL)
        # ==========================================
        rag_chain = RAG_CHAT_PROMPT | active_llm | output_parser
        print(f"rag_chain: {rag_chain}")

        # ==========================================
        # 체인 실행 (.invoke)
        # ==========================================
        answer = await rag_chain.ainvoke({
            "context":context,
            "question":request.message
        })
        # 최종 답변 저장
        data["answer"] = answer
        

        #TODO: response

        return {
            "request": request,
            "response":data
        }


    async def chat_stream(self, payload:ChatRequest):
        """
        스트리밍 응답을 위한 제너레이터 함수
        """

        yield 'data: {"status": "processing", "message": "사용자 질의에서 키워드를 추출하고 있습니다."}\n\n'
        
        # 선택된 모델 인스턴스 가져오기
        provider = payload.llm_config.provider.lower() or "openai"
        active_llm = self.langchain.get(provider)

        # 출력 파서 생성
        output_parser = StrOutputParser()

        # 키워드 추출 진행
        keyword_chain = MANUAL_KEYWORD_EXTRACTION_PROMPT | active_llm | output_parser
        keywords = await keyword_chain.ainvoke({
            "question": payload.message
        })


        yield 'data: {"status": "processing", "message": "임베딩 DB에서 관련 문서를 검색 중입니다..."}\n\n'

        #TODO: RAG 검색 (생략)
        context = MOCK_CONTEXT

        yield 'data: {"status": "generating", "message": "답변을 생성 중입니다..."}\n\n'
        rag_chain = RAG_CHAT_PROMPT | active_llm | output_parser

        answer = ""
        # astream()을 쓰면 응답이 '제너레이터' 형태로 변환
        async for chunk in rag_chain.astream({
            "context":context,
            "question":payload.message
        }): 
            # 조각(chunk)이 생성될 때마다 메인 스레드에 실시간으로 전송(yield)
            # SSE 표준 포맷(data: ... \n\n)에 맞춰서 전송
            # yield f'data: {chunk}\n\n'

            # LLM이 뱉어내는 텍스트 조각(chunk) 중에 만약 문단 바꿈(엔터 키, \n)이 섞여 있으면, 프론트엔드가 파싱하다가 에러 발생
            # -> 해결 이 부분만 json.dumps로 한 겹 싸서 보내시면
            print(chunk)
            answer += chunk
            yield f'data: {json.dumps(chunk, ensure_ascii=False)}\n\n'


        # 스트리밍 종료
        yield 'data: [DONE]\n\n'
        


        