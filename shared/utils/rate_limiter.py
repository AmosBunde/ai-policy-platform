"""Token bucket rate limiter backed by Redis."""
import time

import redis.asyncio as aioredis
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from shared.config.settings import get_settings

# Lua script for atomic token bucket operation
_TOKEN_BUCKET_SCRIPT = """
local key = KEYS[1]
local max_tokens = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(bucket[1])
local last_refill = tonumber(bucket[2])

if tokens == nil then
    tokens = max_tokens
    last_refill = now
end

-- Refill tokens based on elapsed time
local elapsed = now - last_refill
local new_tokens = elapsed * refill_rate
tokens = math.min(max_tokens, tokens + new_tokens)

-- Try to consume one token
if tokens >= 1 then
    tokens = tokens - 1
    redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
    redis.call('EXPIRE', key, math.ceil(max_tokens / refill_rate) + 1)
    return {1, math.floor(tokens), math.ceil((1 - tokens) / refill_rate)}
else
    redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
    redis.call('EXPIRE', key, math.ceil(max_tokens / refill_rate) + 1)
    local retry_after = math.ceil((1 - tokens) / refill_rate)
    return {0, 0, retry_after}
end
"""


class RateLimitConfig:
    """Per-endpoint rate limit configuration."""

    def __init__(
        self,
        max_tokens: int = 60,
        refill_rate: float = 1.0,
        key_prefix: str = "ratelimit",
    ):
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate
        self.key_prefix = key_prefix


# Default per-endpoint limits
DEFAULT_LIMITS: dict[str, RateLimitConfig] = {
    "/api/v1/auth/login": RateLimitConfig(max_tokens=5, refill_rate=0.1),
    "/api/v1/auth/register": RateLimitConfig(max_tokens=3, refill_rate=0.05),
    "/api/v1/search": RateLimitConfig(max_tokens=30, refill_rate=0.5),
}

DEFAULT_CONFIG = RateLimitConfig(max_tokens=60, refill_rate=1.0)


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Token bucket rate limiter middleware using Redis."""

    def __init__(
        self,
        app,
        redis_url: str | None = None,
        endpoint_limits: dict[str, RateLimitConfig] | None = None,
        default_config: RateLimitConfig | None = None,
    ):
        super().__init__(app)
        settings = get_settings()
        self._redis_url = redis_url or settings.redis_url
        self._redis: aioredis.Redis | None = None
        self._script_sha: str | None = None
        self._endpoint_limits = endpoint_limits or DEFAULT_LIMITS
        self._default_config = default_config or DEFAULT_CONFIG

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(self._redis_url, decode_responses=True)
        return self._redis

    def _get_client_key(self, request: Request) -> str:
        """Extract client identifier for rate limiting."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        return ip

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path = request.url.path
        config = self._endpoint_limits.get(path, self._default_config)

        client_key = self._get_client_key(request)
        redis_key = f"{config.key_prefix}:{path}:{client_key}"

        try:
            redis = await self._get_redis()
            now = time.time()
            result = await redis.eval(
                _TOKEN_BUCKET_SCRIPT,
                1,
                redis_key,
                config.max_tokens,
                config.refill_rate,
                now,
            )
            allowed, remaining, retry_after = int(result[0]), int(result[1]), int(result[2])

            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded"},
                    headers={
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(retry_after),
                        "Retry-After": str(retry_after),
                    },
                )

            response = await call_next(request)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(retry_after)
            return response

        except Exception:
            # If Redis is down, allow the request (fail open)
            return await call_next(request)
