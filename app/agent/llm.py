from langchain_core.language_models import BaseChatModel
from langchain_ollama import ChatOllama

from app.infrastructure.config.config import LLMConfig


def create_chat_model(config: LLMConfig) -> BaseChatModel:
    return ChatOllama(
        model=config.model,
        base_url=config.base_url,
        temperature=config.temperature,
        client_kwargs={
            "timeout": config.timeout_seconds,
            "trust_env": False,
        },
        num_ctx=config.num_ctx,
        num_predict=config.num_predict,
    )
