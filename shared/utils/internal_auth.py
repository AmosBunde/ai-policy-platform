"""Service-to-service authentication for internal (non-gateway) services.

Internal services (ingestion, agent, compliance, search, notification) are not
exposed publicly, but network isolation alone is a single point of failure —
one ingress or port-mapping mistake would leave document upload and
crawl-trigger endpoints wide open. Every internal request must therefore carry
a shared token issued to the gateway.

Usage (internal service):
    app = FastAPI(..., dependencies=[Depends(require_internal_token)])

Usage (gateway, outgoing):
    httpx.AsyncClient(headers=internal_auth_headers())
"""

import hmac
import logging

from fastapi import HTTPException, Request, status

from shared.config.settings import get_settings

logger = logging.getLogger(__name__)

INTERNAL_TOKEN_HEADER = "X-Internal-Token"
_MIN_TOKEN_LENGTH = 32

# Paths that must stay reachable without auth: orchestrator probes.
_EXEMPT_PATHS = ("/health",)


def _configured_token() -> str:
    """Return the configured internal token, enforcing minimum length."""
    token = get_settings().internal_service_token
    if token and len(token) < _MIN_TOKEN_LENGTH:
        raise RuntimeError(
            "INTERNAL_SERVICE_TOKEN must be at least 32 characters. "
            "Generate one with: openssl rand -hex 32"
        )
    return token


def internal_auth_headers() -> dict[str, str]:
    """Headers the gateway attaches when calling internal services."""
    token = _configured_token()
    return {INTERNAL_TOKEN_HEADER: token} if token else {}


async def require_internal_token(request: Request) -> None:
    """FastAPI dependency rejecting requests without a valid internal token.

    In development with no token configured, requests are allowed (with a
    warning) so local compose setups keep working. In any other environment
    an unconfigured token fails closed.
    """
    if request.url.path.startswith(_EXEMPT_PATHS):
        return

    expected = _configured_token()
    if not expected:
        if get_settings().app_env == "development":
            logger.warning(
                "INTERNAL_SERVICE_TOKEN not set — allowing unauthenticated "
                "internal request in development only (path=%s)",
                request.url.path,
            )
            return
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service misconfigured: internal authentication not set up",
        )

    provided = request.headers.get(INTERNAL_TOKEN_HEADER, "")
    if not hmac.compare_digest(provided.encode(), expected.encode()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing internal service token",
        )
