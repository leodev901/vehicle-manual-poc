from pydantic import BaseModel, Field


class ManualBrandRequest(BaseModel):
    pass

class ManualLineupRequest(BaseModel):
    brand_id: str = Field(..., description="Brand ID", example="HD")

class ManualModelRequest(BaseModel):
    lineup_id: str = Field(..., description="Lineup ID", example="LX3")
