"""Simple in-memory rate limiter."""
from __future__ import annotations

import threading
import time
from collections import defaultdict
from typing import Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class RateLimiter:
    """Per-client-IP sliding-window limiter."""

    def __init__(self, requests_per_minute: int = 300) -> None:
        self.requests_per_minute = max(1, requests_per_minute)
        self._buckets: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def allow(self, client_id: str) -> Tuple[bool, int]:
        now = time.monotonic()
        window_start = now - 60.0

        with self._lock:
            bucket = self._buckets[client_id]
            bucket[:] = [t for t in bucket if t > window_start]

            if len(bucket) >= self.requests_per_minute:
                retry_after = max(1, int(60 - (now - bucket[0])))
                return False, retry_after

            bucket.append(now)
            return True, 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 300) -> None:
        super().__init__(app)
        self.limiter = RateLimiter(requests_per_minute)

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path

        # Health checks and CORS preflight do not consume the limit.
        if (
            request.method == "OPTIONS"
            or path in {
                "/",
                "/health",
                "/api/health",
                "/api/system/info",
            }
        ):
            return await call_next(request)

        client = request.client.host if request.client else "unknown"
        allowed, retry = self.limiter.allow(client)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too Many Requests",
                    "retry_after_seconds": retry,
                },
                headers={"Retry-After": str(retry)},
            )

        return await call_next(request)