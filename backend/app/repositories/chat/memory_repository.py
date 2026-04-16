

class ChatInMemoryRepository:

    SESSION_STORAGE:dict[str, list[dict[str, str]]] = {}

    def __init__(self):
        pass

