import json


def looks_like_text_tool_call(content: str, tool_names: frozenset[str]) -> bool:
    """Ответ модели — вызов инструмента, записанный текстом вместо tool_calls?"""

    text = content.strip()

    if not text.startswith("{"):
        return False

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return False

    name = data.get("name")
    return isinstance(name, str) and name in tool_names
