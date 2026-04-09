from app.core.config import settings
from openai import OpenAI
from google import genai

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


    