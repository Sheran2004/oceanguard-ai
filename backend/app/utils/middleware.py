"""Request-ID + structured access-log middleware."""
from __future__ import annotations

import logging
import secrets
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.utils.logging import log_event


_access_logger = logging.getLogger("oceanguard.access")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique request ID to every request and surface it in the response."""

    async def dispatch(self, request: Request, call_next) -> Response:
        rid = request.headers.get("x-request-id") or secrets.token_hex(8)
        request.state.request_id = rid

        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:  # pragma: no cover - propagated by global handler
            duration_ms = (time.perf_counter() - start) * 1000
            log_event(
                _access_logger, logging.ERROR, "http.request.failed",
                request_id=rid, method=request.method, path=request.url.path,
                duration_ms=round(duration_ms, 2), error=str(exc),
            )
            raise
        duration_ms = (time.perf_counter() - start) * 1000

        response.headers["x-request-id"] = rid
        log_event(
            _access_logger, logging.INFO, "http.request",
            request_id=rid, method=request.method, path=request.url.path,
            status=response.status_code, duration_ms=round(duration_ms, 2),
        )
        return response