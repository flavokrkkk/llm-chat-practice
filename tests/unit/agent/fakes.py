from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import BaseMessage
from pydantic import Field


class ToolBindableFakeModel(GenericFakeChatModel):
    """Фейковая модель, которую можно передать в build_graph."""

    def bind_tools(self, tools, **kwargs):
        return self


class RecordingFakeModel(ToolBindableFakeModel):
    calls: list[list[BaseMessage]] = Field(default_factory=list)

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        self.calls.append(messages)
        return super()._generate(messages, stop, run_manager, **kwargs)


class FailingFakeModel(ToolBindableFakeModel):
    """Модель, которая падает с заданной ошибкой на любой вызов."""

    error: Exception

    def _generate(self, *args, **kwargs):
        raise self.error

    async def _agenerate(self, *args, **kwargs):
        raise self.error
