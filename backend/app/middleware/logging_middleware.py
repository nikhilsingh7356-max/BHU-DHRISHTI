import time
import logging
from fastapi import Request

logger = logging.getLogger("bhudrishti")


class LoggingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request = Request(scope, receive)
        start_time = time.time()
        method = scope.get("method", "")
        path = scope.get("path", "")

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_code = message.get("status", 0)
                duration = (time.time() - start_time) * 1000
                logger.info(
                    f"{method} {path} -> {status_code} ({duration:.2f}ms)"
                )
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(f"{method} {path} -> ERROR ({duration:.2f}ms): {str(e)}")
            raise
