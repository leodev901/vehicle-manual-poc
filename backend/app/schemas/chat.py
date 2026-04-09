from pydantic import BaseModel, Field

class LlmConfig(BaseModel):
    provider: str | None = Field(default=None, description="Provider", example="openai")
    model:str | None = Field(default=None, description="Model", example="gpt-5-nano")

class ChatRequest(BaseModel):
    session_id: str | None = Field(default=None, description="Session ID", example="session-1234567890") 
    model_id: str | None = Field(default=None, description="Model ID", example="LX3HEV")
    llm_config: LlmConfig | None = Field(default=None, description="LLM Config")
    message: str = Field(..., description="Message", example="엔진오일 교환 주기는 어떻게 되나요?")


class ChatResponse(BaseModel):
    session_id: str
    model_id: str
    result: str
    