from pydantic import BaseModel, Field, field_validator


class HealthzRequest(BaseModel):
    schema_name: str | None = Field(default=None, description="Database schema name", examples=[""])
    table_name: str | None = Field(default=None, description="Database table name", examples=[""])
    

    @field_validator("schema_name", mode="before")
    @classmethod
    def validate_schema_name(cls, v: str | None) -> str :
        # v가 None이면 ""이 되고, 글자면 앞뒤 공백을 자릅니다.
        normalized_v = str(v or "").strip()
        if not normalized_v:
            return "vehicle_manual_rag"
        # SQL 인젝션 방지 예시: 띄어쓰기 금지    
        if " " in normalized_v:
            raise ValueError("스키마 이름에는 공백이 들어갈 수 없습니다.")
        return normalized_v.lower()

    @field_validator("table_name", mode="before")
    @classmethod
    def validate_table_name(cls, v: str | None) -> str :
        # v가 None이면 ""이 되고, 글자면 앞뒤 공백을 자릅니다.
        normalized_v = str(v or "").strip()
        if not normalized_v:
            return "models"
        # SQL 인젝션 방지 예시: 띄어쓰기 금지    
        if " " in normalized_v:
            raise ValueError("테이블 이름에는 공백이 들어갈 수 없습니다.")
        return normalized_v.lower()