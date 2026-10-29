from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, RedisDsn, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict
from sqlalchemy import URL

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

ENV_FILE = BASE_DIR / ".env"


class RedisConfig(BaseModel):
    url: RedisDsn
    cache_ttl_seconds: int = 3600


class DatabaseConfig(BaseModel):
    name: str
    user: str
    password: str
    host: str
    port: int
    pool_size: int = 5
    max_overflow: int = 10
    pool_pre_ping: bool = True
    echo: bool = False

    def _build_url(self, driver: str) -> URL:
        return URL.create(
            drivername=driver,
            username=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.name,
        )

    @property
    def sqlalchemy_url(self) -> URL:
        return self._build_url("postgresql+asyncpg")

    @property
    def psycopg_url(self) -> str:
        return self._build_url("postgresql").render_as_string(hide_password=False)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE, extra="ignore", env_nested_delimiter="__"
    )

    db: DatabaseConfig
    redis: RedisConfig
    cors_origins: Annotated[list[str], NoDecode]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, val: str | list[str]) -> list[str]:
        if isinstance(val, list):
            return val

        return [origin for s in val.split(",") if (origin := s.strip())]


settings = Settings()  # pyright: ignore[reportCallIssue]
