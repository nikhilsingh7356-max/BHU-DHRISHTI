from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres123@localhost:5432/bhudrishti"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres123@localhost:5432/bhudrishti"
    SECRET_KEY: str = "bhudrishti-secret-key-change-in-production-2024"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CORS_ORIGINS: str = '["http://localhost:3000","http://localhost:3001","http://localhost:3002","http://localhost:3003"]'
    APP_NAME: str = "Bhu-Drishti"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 50

    @property
    def cors_origins_list(self) -> List[str]:
        return json.loads(self.CORS_ORIGINS)

    @property
    def async_database_url(self) -> str:
        url = self.DATABASE_URL
        if url.startswith("postgresql://") or url.startswith("postgres://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
