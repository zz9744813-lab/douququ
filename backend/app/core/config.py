from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./zongmen.db"
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2000
    llm_timeout: int = 30
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    max_actions_per_turn: int = 3
    default_world_seed: int = 42

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()