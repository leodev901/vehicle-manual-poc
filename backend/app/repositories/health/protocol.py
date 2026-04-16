from typing import Protocol, List, Dict, Any


# HealthzRepository가 구현해야 하는 최소한의 메서드 명세서 (Duck Typing 구조)
class HealthzRepositoryProtocol(Protocol):
    async def health_check(self, schema_name:str, table_name:str) -> Dict[str, Any]:
        ...