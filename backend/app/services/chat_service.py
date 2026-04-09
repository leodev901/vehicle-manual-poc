
from supabase import Client

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
            "request": request,
            "response":data
            }
        