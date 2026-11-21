import pytest

from app.agent.guards import looks_like_text_tool_call

TOOL_NAMES = frozenset({"get_balance"})


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        pytest.param('{"name": "get_balance", "arguments": {}}', True, id="tool_call"),
        pytest.param(
            ' {"name": "get_balance", "arguments": {}} ', True, id="with_spaces"
        ),
        pytest.param("Ваш баланс — 798 ₸", False, id="plain_text"),
        pytest.param('{"name": "unknown_tool"}', False, id="unknown_tool"),
        pytest.param('{"name": "get_balance"', False, id="broken_json"),
        pytest.param("", False, id="empty"),
        pytest.param('{"name": ["get_balance"]}', False, id="name_not_string"),
    ],
)
def test_looks_like_text_tool_call(content, expected):
    assert looks_like_text_tool_call(content, TOOL_NAMES) is expected
