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
