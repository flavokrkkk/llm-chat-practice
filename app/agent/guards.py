def looks_like_text_tool_call(content: str, tool_names: set[str]) -> bool:
    """Ответ модели — вызов инструмента, записанный текстом вместо tool_calls?"""
    return False
