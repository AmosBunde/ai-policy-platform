"""Consistent error envelope across all services.

Every service registers these handlers so clients always receive the same
JSON shape — {"detail": ..., "request_id": ...} — and stack traces never
leak into response bodies. The full traceback still goes to the structured
log, correlated by request_id.
"""

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from shared.utils.logging import current_request_id

logger = structlog.get_logger()


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None) or current_request_id()


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all: log the traceback, return an opaque 500 envelope."""
    await logger.aexception(
        "unhandled_exception",
        method=request.method,
        path=request.url.path,
        error_type=type(exc).__name__,
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "request_id": _request_id(request),
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach the shared error envelope to a FastAPI app."""
    app.add_exception_handler(Exception, unhandled_exception_handler)
