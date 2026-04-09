from pydantic import BaseModel

class ChatRequest(BaseModel):
    session_id: str | None = None 
    model_id: str | None = None
    message: str


class ChatResponse(BaseModel):
    session_id: str
    model_id: str
    result: str
    