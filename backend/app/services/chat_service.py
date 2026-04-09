
from supabase import Client

from app.schemas.chat import ChatRequest
from app.prompts.chat_prompts import MANUAL_KEYWORD_EXTRACTION_PROMPT

class ChatService:

    @staticmethod
    def chat(request: ChatRequest, supabase: Client, llm: dict):

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
            data["keywords"] = keywords               
        
        #TODO: Kewyrod Extraction w/ LLM
        #TODO: RAG
        #TODO: LLM
        #TODO: response

        return {
            "request": request,
            "response":data
            }
        