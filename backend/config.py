from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    chroma_host: str = "chromadb"
    chroma_port: int = 8000
    anthropic_api_key: str
    clerk_jwks_url: str
    frontend_url: str = "http://localhost"

    class Config:
        env_file = ".env"


settings = Settings()
