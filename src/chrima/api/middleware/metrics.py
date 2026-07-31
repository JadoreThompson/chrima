import time

from prometheus_client import start_http_server
from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from chrima.monitoring import http_request_duration_seconds, http_requests_total
from config import PROMETHEUS_METRICS_PORT


class MetricsMiddleware:
    def __init__(self, app: ASGIApp, *, excluded_paths: set[str] | None = None) -> None:
        self.app = app
        self._excluded_paths = excluded_paths or set()
        start_http_server(port=PROMETHEUS_METRICS_PORT)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)

        if request.url.path in self._excluded_paths:
            await self.app(scope, receive, send)
            return

        method = request.method
        path = request.url.path

        start = time.perf_counter()

        status_code: int | None = None

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code

            if message["type"] == "http.response.start":
                status_code = message["status"]

            await send(message)

        await self.app(scope, receive, send_wrapper)

        duration = time.perf_counter() - start

        route = scope.get("route")
        if route is not None:
            path = getattr(route, "path", path)

        status = str(status_code or 500)

        http_requests_total.labels(
            method=method,
            path=path,
            status=status,
        ).inc()

        http_request_duration_seconds.labels(
            method=method,
            path=path,
            status=status,
        ).observe(duration)
