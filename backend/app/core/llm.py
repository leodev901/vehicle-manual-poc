from app.core.config import settings
from openai import OpenAI
from google import genai
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

from app.base.logger import logger


def create_llm_client():
    clients = {}

    if getattr(settings,"OPENAI_API_KEY",None):
        clients["openai"] = OpenAI(api_key=settings.OPENAI_API_KEY)
        logger.info("OpenAI Client Created")

    if getattr(settings,"GEMINI_API_KEY",None):
        clients["gemini"] = genai.Client(api_key=settings.GEMINI_API_KEY)
        logger.info("Gemini Client Created")

    return clients


def create_langchain_client():
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