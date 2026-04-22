from app.core.config import settings
from openai import OpenAI
from google import genai
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chat_models import init_chat_model

from app.base.logger import logger


def create_llm_clients():
    clients = {}

    if getattr(settings,"OPENAI_API_KEY",None):
        clients["openai"] = OpenAI(api_key=settings.OPENAI_API_KEY)
        logger.info("OpenAI Client Created")

    if getattr(settings,"GEMINI_API_KEY",None):
        clients["gemini"] = genai.Client(api_key=settings.GEMINI_API_KEY)
        logger.info("Gemini Client Created")

    return clients


# 모델별로 다른 생성자로 생성하는 langchin 0.1 버전 -> 미사용
def create_langchain_clients():
    clients = {}
    if getattr(settings,"OPENAI_API_KEY",None):
        clients["openai"] = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=getattr(settings,"OPENAI_MODEL","gpt-5-nano"),
            # temperature=0.7,
            # max_tokens=1000,
            # timeout=30,
        )
        logger.info("LangChain OpenAI Client Created")
    
    if getattr(settings,"GEMINI_API_KEY",None):
        clients["gemini"] = ChatGoogleGenerativeAI(
            api_key=settings.GEMINI_API_KEY,
            model=getattr(settings,"GEMINI_MODEL","gemini-2.5-flash-lite"),
            # temperature=0.7,
            # max_tokens=1000,
            # timeout=30,
        )
        logger.info("LangChain Gemini Client Created")

    return clients



# LangChain 0.2 버전
def create_chat_models():
    models = {}
    if getattr(settings,"OPENAI_API_KEY",None):
        models["openai"] = init_chat_model(
            model=getattr(settings,"OPENAI_MODEL","gpt-5-nano"),
            model_provider="openai",
            api_key=settings.OPENAI_API_KEY,
            # temperature=0.7,
            # max_tokens=1000,
            # timeout=30,
        )
        logger.info("LangChain OpenAI Client Created")
    
    if getattr(settings,"GEMINI_API_KEY",None):
        models["gemini"] = init_chat_model(
            model=getattr(settings,"GEMINI_MODEL","gemini-2.5-flash-lite"),
            model_provider="google_genai",
            api_key=settings.GEMINI_API_KEY,
            # temperature=0.7,
            # max_tokens=1000,
            # timeout=30,
        )
        logger.info("LangChain Gemini Client Created")

    return models
