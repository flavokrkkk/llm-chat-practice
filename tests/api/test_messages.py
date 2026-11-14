import pytest

from tests.api.helpers import create_chat, create_message, login

pytestmark = [pytest.mark.api, pytest.mark.llm]


async def test_send_message_returns_assistant_reply(client, make_user):
    headers = await login(client, await make_user())
    chat_id = await create_chat(client, headers)

    reply = await create_message(
        client, chat_id=chat_id, headers={**headers, "Idempotency-Key": "key-1"}
    )

    assert reply["role"] == "assistant"
    assert reply["content"] != ""
    assert reply["chat_id"] == chat_id


async def test_repeat_with_same_key_returns_same_reply(client, make_user):
    headers = await login(client, await make_user())
    chat_id = await create_chat(client, headers)
    key_headers = {**headers, "Idempotency-Key": "key-1"}

    first = await create_message(client, chat_id=chat_id, headers=key_headers)
    second = await create_message(client, chat_id=chat_id, headers=key_headers)

    assert second["id"] == first["id"]
    assert second["content"] == first["content"]


async def test_same_key_in_other_chat_creates_new_reply(client, make_user):
    headers = await login(client, await make_user())
    chat_a = await create_chat(client, headers)
    chat_b = await create_chat(client, headers)

    reply_a = await create_message(
        client, chat_id=chat_a, headers={**headers, "Idempotency-Key": "key-1"}
    )
    reply_b = await create_message(
        client, chat_id=chat_b, headers={**headers, "Idempotency-Key": "key-1"}
    )

    assert reply_b["id"] != reply_a["id"]
    assert reply_b["chat_id"] == chat_b
