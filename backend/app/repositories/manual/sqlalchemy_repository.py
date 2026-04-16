class ManualSqlAlchemyRepository:
    def __init__(self):
        pass

    async def list_brands(self):
        raise NotImplementedError

    async def list_lineups(self, brand_id:str):
        raise NotImplementedError

    async def list_models(self, lineup_id:str):
        raise NotImplementedError