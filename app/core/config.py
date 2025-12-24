from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./mod_checker.db"

    class Config:
        case_sensitive = True

settings = Settings()
