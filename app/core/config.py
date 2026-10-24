import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    database_url: str = os.environ.get(
        "DATABASE_URL", "postgresql://llm-chat:llm-chat@localhost:5433/llm-chat"
    )
    cors_origins: list[str] = field(
        default_factory=lambda: os.environ.get(
            "CORS_ORIGINS", "http://localhost:5173"
        ).split(",")
    )
    redis_url: str = (
        f"redis://{os.environ.get('REDIS_HOST', "redis")}:{os.environ.get('REDIS_PORT', "6379")}"
    )
    cache_ttl_seconds = 3600


settings = Settings()
