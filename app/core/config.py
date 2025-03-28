 # app/core/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI Yandex Audio Uploader"
    API_V1_STR: str = "/api/v1"

    # Database
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_URI: str | None = None

    # JWT
    SECRET_KEY: str # openssl rand -hex 32
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # Yandex OAuth
    YANDEX_CLIENT_ID: str
    YANDEX_CLIENT_SECRET: str
    YANDEX_REDIRECT_URI: str # e.g. http://localhost:8000/api/v1/auth/yandex/callback

    # Superuser
    FIRST_SUPERUSER_EMAIL: str | None = None
    FIRST_SUPERUSER_YANDEX_ID: str | None = None

    # File Uploads
    UPLOAD_DIR: str = "uploads"

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()

if not settings.DATABASE_URI:
    settings.DATABASE_URI = (
        f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@"
        f"{settings.POSTGRES_SERVER}/{settings.POSTGRES_DB}"
    )
