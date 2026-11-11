import os
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, Field, RedisDsn, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict
from sqlalchemy import URL

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

ENV_FILE = BASE_DIR / ".env"

cp_count = os.cpu_count()
CP_DEFAULT = 4


def _default_hash_concurrency() -> int:
    cpus = os.process_cpu_count() or 4
    return max(1, cpus - 1)


class CheckpointerConfig(BaseModel):
    pool_min_size: int = Field(default=1, ge=0)
    pool_max_size: int = Field(default=10, gt=0)


class LLMConfig(BaseModel):
    base_url: str = "http://localhost:11434"
    model: str
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    timeout_seconds: float = Field(default=60.0, gt=0)
    num_ctx: int = Field(default=8192, gt=0)
    num_predict: int = Field(default=1024, gt=0)


class PasswordHashConfig(BaseModel):
    max_concurrency: int = Field(default_factory=_default_hash_concurrency, ge=1)


class TransferConfig(BaseModel):
    demo_delay_seconds: float = 0.0


class RedisConfig(BaseModel):
    url: RedisDsn
    cache_ttl_seconds: int = 3600


class JWTConfig(BaseModel):
    secret: SecretStr
    access_token_ttl_minutes: int = Field(default=15, gt=0)
    refresh_token_ttl_days: int = Field(default=30, gt=0)
    algorithm: Literal["HS256"] = "HS256"


class DatabaseConfig(BaseModel):
    name: str
    user: str
    password: str
    host: str
    port: int
    pool_size: int = Field(default=5, gt=0)
    max_overflow: int = Field(default=10, ge=0)
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
    jwt: JWTConfig
    llm: LLMConfig
    cors_origins: Annotated[list[str], NoDecode]
    transfer: TransferConfig = Field(default_factory=TransferConfig)
    password_hash: PasswordHashConfig = Field(default_factory=PasswordHashConfig)
    checkpointer: CheckpointerConfig = Field(default_factory=CheckpointerConfig)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, val: str | list[str]) -> list[str]:
        if isinstance(val, list):
            return val

        return [origin for s in val.split(",") if (origin := s.strip())]


settings = Settings()  # pyright: ignore[reportCallIssue]
