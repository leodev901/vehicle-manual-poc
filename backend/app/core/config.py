from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8",extra="ignore")

    database_url: str
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_recycle: int = 3600
    db_echo: bool = False

    SUPABASE_URL:str
    SUPABASE_KEY:str

    OPENAI_API_KEY:str
    OPENAI_MODEL:str

    GEMINI_API_KEY:str
    GEMINI_MODEL:str


settings = Settings()
