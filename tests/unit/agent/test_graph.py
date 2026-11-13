import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, BaseMessage
from pydantic import Field


class RecordingFakeModel(GenericFakeChatModel):
    calls: list[list[BaseMessage]] = Field(default_factory=list)

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        self.calls.append(messages)
        return super()._generate(messages, stop, run_manager, **kwargs)


@pytest.fixture
def finance_model():
    return RecordingFakeModel(
        messages=iter(
            [
                AIMessage("Здравствуйте! Чем могу помочь?"),
                AIMessage("Ваш вопрос принят."),
            ]
        )
    )
