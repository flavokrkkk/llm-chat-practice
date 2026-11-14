from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import BaseMessage
from pydantic import Field


class RecordingFakeModel(GenericFakeChatModel):
    calls: list[list[BaseMessage]] = Field(default_factory=list)

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        self.calls.append(messages)
        return super()._generate(messages, stop, run_manager, **kwargs)


class FailingFakeModel(GenericFakeChatModel):
    """Модель, которая падает с заданной ошибкой на любой вызов."""

    error: Exception

    def _generate(self, *args, **kwargs):
        raise self.error

    async def _agenerate(self, *args, **kwargs):
        raise self.error
