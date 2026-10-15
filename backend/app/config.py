from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Shelfwise API"
    app_version: str = "1.0.0"
    environment: str = "local"
    database_url: str = "postgresql+psycopg://shelfwise:shelfwise@localhost:5432/shelfwise"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
