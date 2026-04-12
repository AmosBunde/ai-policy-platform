"""Structured logging with secret masking and request ID middleware."""
import logging
import re
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# Patterns to mask in log output
_MASK_PATTERNS = [
    (re.compile(r'(password["\s:=]+)[^\s,}"]+', re.IGNORECASE), r"\1***"),
    (re.compile(r'(token["\s:=]+)[^\s,}"]+', re.IGNORECASE), r"\1***"),
    (re.compile(r'(api_key["\s:=]+)[^\s,}"]+', re.IGNORECASE), r"\1***"),
    (re.compile(r'(Authorization["\s:]+)\S+(\s+\S+)?', re.IGNORECASE), r"\1***"),
    (re.compile(r'(secret["\s:=]+)[^\s,}"]+', re.IGNORECASE), r"\1***"),
]

# Auth endpoints where request bodies should never be logged
_AUTH_PATHS = {"/api/v1/auth/login", "/api/v1/auth/register", "/api/v1/auth/refresh"}


def mask_secrets(text: str) -> str:
    """Mask sensitive patterns in log text."""
    for pattern, replacement in _MASK_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _mask_processor(logger, method_name, event_dict):
    """Structlog processor that masks secrets in log events."""
    if "event" in event_dict and isinstance(event_dict["event"], str):
        event_dict["event"] = mask_secrets(event_dict["event"])
    # Mask any string values in the dict
    for key, value in list(event_dict.items()):
        if isinstance(value, str) and key not in ("logger", "level", "timestamp"):
            event_dict[key] = mask_secrets(value)
    return event_dict


def configure_logging(service_name: str, level: str = "INFO") -> None:
    """Configure structlog with JSON processing in prod, colored output in dev."""
    from shared.config.settings import get_settings
    settings = get_settings()
    is_prod = settings.app_env == "production"

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        _mask_processor,
    ]

    if is_prod:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Bind service name to all log entries
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(service=service_name)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware that generates a UUID request_id for each request.

    - Adds request_id to structlog context vars for all log entries
    - Returns request_id in X-Request-ID response header
    - Skips logging request bodies on auth endpoints
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = str(uuid.uuid4())
        structlog.contextvars.bind_contextvars(request_id=request_id)

        logger = structlog.get_logger()
        path = request.url.path

        if path not in _AUTH_PATHS:
            await logger.ainfo(
                "request_started",
                method=request.method,
                path=path,
            )

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        await logger.ainfo(
            "request_completed",
            method=request.method,
            path=path,
            status_code=response.status_code,
        )

        structlog.contextvars.unbind_contextvars("request_id")
        return response
