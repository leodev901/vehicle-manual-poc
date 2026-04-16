class ManualMockRepository:
    def __init__(self):
        pass

    async def list_brands(self):
        return [
            {"id": "HD", "name": "현대"},
            {"id": "KB", "name": "기아"},
            {"id": "GM", "name": "제네시스"},
        ]

    async def list_lineups(self, brand_id:str):
        return [
            {"id": "LX3", "name": "쏘나타"},
            {"id": "KX3", "name": "K5"},
            {"id": "GX3", "name": "G80"},
        ]

    async def list_models(self, lineup_id:str):
        return [
            {"id": "LX31", "name": "쏘나타 1"},
            {"id": "LX32", "name": "쏘나타 2"},
            {"id": "LX33", "name": "쏘나타 3"},
        ]
        