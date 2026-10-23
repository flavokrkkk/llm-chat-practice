import asyncpg


class ChatService:
    def __init__(self, session: asyncpg.Connection):
        self.session = session
