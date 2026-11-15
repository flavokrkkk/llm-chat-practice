import httpx
from langchain_core.language_models import BaseChatModel
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from ollama import ResponseError

from app.infrastructure.config.config import LLMConfig


class LLMProviderError(Exception):
    """Ошибка ответа провайдера LLM: 4xx/5xx, недоступность."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


LLM_PROVIDER_ERRORS: tuple[type[Exception], ...] = (
    ResponseError,
    httpx.HTTPError,
    LLMProviderError,
)


def _create_ollama(config: LLMConfig) -> BaseChatModel:
    return ChatOllama(
        model=config.model,
        base_url=config.base_url,
        temperature=config.temperature,
        client_kwargs={
            "timeout": config.timeout_seconds,
            "trust_env": False,
        },
        num_ctx=config.num_ctx,
        num_predict=config.max_output_tokens,
    )


def _create_nvidia(config: LLMConfig) -> BaseChatModel:
    if config.api_key is None:
        raise RuntimeError("api_key is required for nvidia provider")

    api_url = "https://integrate.api.nvidia.com/v1"

    return ChatOpenAI(
        model=config.model,
        api_key=config.api_key,
        base_url=api_url,
        temperature=config.temperature,
        max_completion_tokens=config.max_output_tokens,
        openai_proxy="http://127.0.0.1:10801",
        http_socket_options=(),
        timeout=60.0,
    )


def create_chat_model(config: LLMConfig) -> BaseChatModel:
    match config.provider:
        case "ollama":
            return _create_ollama(config)
        case "nvidia":
            return _create_nvidia(config)
