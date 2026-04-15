from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_URL: str = ""
    REDIS_URL: str = ""
    JWT_SECRET: str = "changeme"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    EXCHANGE_RATE_API_KEY: str = "dummy"
    EXCHANGE_RATE_API_URL: str = "https://openexchangerates.org/api"
    EXCHANGE_RATE_CACHE_TTL: int = 3600
    EXCHANGE_RATE_API_TIMEOUT: int = 10
    ENVIRONMENT: str = "development"
    PORT: int = 8000

    @property
    def async_database_url(self) -> str:
        url = self.DB_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    class Config:
        env_file = ".env"


settings = Settings()
