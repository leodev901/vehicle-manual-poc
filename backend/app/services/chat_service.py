
from supabase import Client
from langchain_core.output_parsers import StrOutputParser

from app.schemas.chat import ChatRequest
from app.prompts.chat_prompts import MANUAL_KEYWORD_EXTRACTION_PROMPT, RAG_CHAT_PROMPT, MOCK_CONTEXT


class ChatService:

    @staticmethod
    def chat(request: ChatRequest, supabase: Client, llm: dict):

        #TODO: Kewyrod Extraction w/ LLM
        data = {}
        #TODO: session history 
        provider = request.llm_config.provider
        model = request.llm_config.model

        if provider.upper() == "OPENAI":
            client = llm[provider]
            response = client.responses.create(
                model=model,
                input=MANUAL_KEYWORD_EXTRACTION_PROMPT.format(
                    question=request.message
                )
            )
            keywords = response.output_text.strip()

        elif provider.upper() == "GEMINI":
            client = llm[provider]
            response = client.models.generate_content(
                model=model,
                contents=MANUAL_KEYWORD_EXTRACTION_PROMPT.format(
                    question=request.message
                )
            )
            keywords = response.text.strip()
        # 키워드 결과 담기
        data["keywords"] = keywords 
        
        
        #TODO: RAG
        # 생략
        context = MOCK_CONTEXT
        
        #TODO: LLM (최종 답변 생성)
        
        
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
            
            }
    
    @staticmethod
    def chat_langchain(request: ChatRequest, supabase: Client, langchain: dict):
        """
        LangChain을 사용하여 Chat을 workflow를 수행합니다.
        """
        data = {}

        provider = request.llm_config.provider.lower() or "openai"
        
        # ==========================================
        # 1. 선택된 LangChain 모델 인스턴스 가져오기
        # ==========================================
        active_llm = langchain.get(provider)


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

        # ==========================================
        # 체인 실행 (.invoke) -> 프롬프트 채우기, API 호출, 텍스트 파싱이 한방에 처리됨!
        # ==========================================
        # 프롬프트 템플릿에 들어갈 변수만 딕셔너리로 넘겨주면, 
        # 프롬프트 완성 -> 모델 호출 -> 텍스트 추출이 한 번에 처리됩니다.
        keywords = keyword_chain.invoke({
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

        answer = rag_chain.invoke({
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
        

        