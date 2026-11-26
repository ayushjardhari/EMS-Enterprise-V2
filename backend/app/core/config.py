"""
Central application configuration.

All settings are read from environment variables (populated from .env via
docker-compose's env_file). Nothing here should ever contain a real secret —
defaults exist only so the app fails loudly and obviously in dev if .env is
missing, not so they're safe to use anywhere real.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Postgres ---
    POSTGRES_USER: str = "ems_admin"
    POSTGRES_PASSWORD: str = "changeme"
    POSTGRES_DB: str = "employee_management"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432

    # --- MinIO ---
    MINIO_HOST: str = "minio"
    MINIO_API_PORT: int = 9000
    MINIO_ROOT_USER: str = "minio_admin"
    MINIO_ROOT_PASSWORD: str = "changeme"
    MINIO_BUCKET_NAME: str = "employee-documents"

    # --- Auth ---
    JWT_SECRET_KEY: str = "changeme"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 120

    # --- Embeddings / semantic search ---
    # EMBEDDING_DIM must match the vector(N) column created in migration 0004.
    # Changing the model to one with a different dimension needs a new migration.
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384
    AUTO_INDEX_ON_UPLOAD: bool = True

    # --- LLM (OpenAI-compatible chat API; Groq free plan by default) ---
    # Leave LLM_API_KEY empty to disable the LLM: explanations then fall back to templates.
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.groq.com/openai/v1"
    LLM_MODEL: str = "openai/gpt-oss-20b"
    LLM_REASONING_EFFORT: str = "low"   # sent only if non-empty; set to "" for models that reject it
    LLM_TIMEOUT_SECONDS: float = 30.0

    # --- CORS ---
    CORS_ORIGINS: str = "http://localhost:5173"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
