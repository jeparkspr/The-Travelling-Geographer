from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/travelling_geographer"
    MEDIA_DIR: str = "/app/media"
    NOMINATIM_URL: str = "https://nominatim.openstreetmap.org"
    APP_NAME: str = "The Travelling Geographer"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB in bytes
    THUMBNAIL_SIZE: tuple = (800, 800)

    # Auth / JWT
    JWT_SECRET_KEY: str = "CHANGE-ME-in-production-use-a-random-64-char-string"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
