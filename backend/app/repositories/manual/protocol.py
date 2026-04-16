from typing import Protocol, List, Dict, Any

# ManualRepository가 구현해야 하는 최소한의 메서드 명세서 (Duck Typing 구조)
# 이 형태만 만족하면 실제 DB 연결 로직이 달라도 교체 가능합니다.
class ManualRepositoryProtocol(Protocol):
    async def list_brands(self) -> List[Dict[str, Any]]:
        ...
    async def list_lineups(self, brand_id:str) -> List[Dict[str, Any]]:
        ...
    async def list_models(self, lineup_id:str) -> List[Dict[str, Any]]:
        ...

#