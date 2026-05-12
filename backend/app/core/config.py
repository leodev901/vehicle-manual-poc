from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8",extra="ignore")

    APP_NAME: str = 'vehicle-manual-poc'
    APP_ENV: str = 'local'
    APP_LOG_LEVEL: str = 'DEBUG'

    database_url: str  | None = None
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_recycle: int = 3600
    db_echo: bool = False

    SUPABASE_URL:str | None = None
    SUPABASE_KEY:str | None = None

    OPENAI_API_KEY:str | None = None
    OPENAI_MODEL:str | None = None

    GEMINI_API_KEY:str | None = None
    GEMINI_MODEL:str | None = None

    XAI_API_KEY:str | None = None
    XAI_MODEL:str | None = None

    #HuggingFace
    HF_INFERENCE_URL:str = "https://leodev901-inference-server.hf.space/api/v1/embed"
    HF_TOKEN:str  | None = None

    # LangSmith 설정 (선택적 - 없으면 트레이싱 비활성화)
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "vehicle-manual-poc"


    ENABLE_OTEL_DIRECT: bool = False
    GRAFANA_ENDPOINT: str="https://otlp-gateway-prod-ap-northeast-0.grafana.net/otlp/v1/logs"
    GRAFANA_INSTANCE_ID: int = 1556283
    GRAFANA_API_TOKEN: str = ""



settings = Settings()
