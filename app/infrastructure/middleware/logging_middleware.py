import logging
import re
import time
from uuid import uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.request_context import request_id_var
from app.infrastructure.errors.error_handlers import INTERNAL_ERROR_CODE, error_response

_REQUEST_ID_RE = re.compile(r"[A-Za-z0-9_-]{1,64}")

logger = logging.getLogger(__name__)


class RequestIdMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        # Храним ссылку на следующее звено в цепочке (следующий middleware или сам FastAPI)
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))

        raw = headers.get(b"x-request-id", b"").decode("latin1")
        request_id = raw if _REQUEST_ID_RE.fullmatch(raw) else uuid4().hex

        token = request_id_var.set(request_id)

        start_time = time.perf_counter()
        status_code = 500
        response_started = False

        async def custom_send(message: Message) -> None:
            nonlocal status_code, response_started

            if message["type"] == "http.response.start":
                status_code = message["status"]
                response_started = True
                response_headers = list(message.get("headers", []))
                response_headers.append((b"x-request-id", request_id.encode("latin1")))
                message["headers"] = response_headers

            await send(message)

        try:
            await self.app(scope, receive, custom_send)
        except Exception:
            logger.exception("Необработанное исключение при обработке запроса")
            if response_started:
                raise
            response = error_response(
                status_code=500,
                error_code=INTERNAL_ERROR_CODE,
                message="Internal server error",
            )
            await response(scope, receive, custom_send)
        finally:
            process_time = (time.perf_counter() - start_time) * 1000
            method = scope.get("method")
            path = scope.get("path")

            logger.info("%s %s -> %s (%.2fms)", method, path, status_code, process_time)
            request_id_var.reset(token)
