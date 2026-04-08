from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_recycle: int = 3600
    db_echo: bool = False

    SUPABASE_URL:str = "https://bhxwivkmovmgptmuttbb.supabase.co"
    SUPABASE_KEY:str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJoeHdpdmttb3ZtZ3B0bXV0dGJiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NDA1ODEzNCwiZXhwIjoyMDc5NjM0MTM0fQ.toXpX7fo1GWTGmhSGSWDdecI_akc6JqozDKegqtfkvE"




settings = Settings()
