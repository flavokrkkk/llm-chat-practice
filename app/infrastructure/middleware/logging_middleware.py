from collections.abc import MutableMapping
from typing import Any
from uuid import uuid4

from starlette.types import ASGIApp, Receive, Scope, Send

Message = MutableMapping[str, Any]


class IdentificationRequestLogMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        # Храним ссылку на следующее звено в цепочке (следующий middleware или сам FastAPI)
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] in ("http", "websocket") and scope["scheme"] in ("http", "ws"):

            async def custom_send(message: Message) -> None:
                request_id = str(uuid4())

                if message["type"] == "http.response.start":
                    message["headers"].append(("X-Request-ID", request_id))

                await send(message)

            await self.app(scope, receive, custom_send)

        else:
            await self.app(scope, receive, send)
