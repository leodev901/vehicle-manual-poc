from typing import TypedDict


class ChatMessage(TypedDict):
    role: str
    content: str


class SessionMemory:
    def __init__(self, maxsize: int = 10):
        self.maxsize = maxsize
        self.session_memory: dict[str, list[ChatMessage]] = {}

    def get_memory(self, session_id: str) -> list[ChatMessage]:
        if session_id not in self.session_memory:
            self.session_memory[session_id] = []
        return self.session_memory[session_id]

    def add_memory(self, session_id: str, role: str, content: str) -> None:
        message: ChatMessage = {
            "role": role,
            "content": content,
        }

        memory = self.get_memory(session_id)
        memory.append(message)

        if len(memory) > self.maxsize:
            self.session_memory[session_id] = memory[-self.maxsize:]


session_memory = SessionMemory()
