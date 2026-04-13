"""RegulatorAI API Gateway Service."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from shared.config.settings import get_settings
from shared.utils.logging import RequestIdMiddleware, configure_logging
from src.middleware.security import SecurityHeadersMiddleware
from src.routes import auth, documents, health, reports, search, users

settings = get_settings()

# Configure structured logging
configure_logging("gateway-service", settings.log_level)
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    logger.info("Gateway service starting up")
    yield
    logger.info("Gateway service shutting down")


app = FastAPI(
    title="RegulatorAI API Gateway",
    description="AI Policy Research & Compliance Automation Platform",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Request ID middleware
app.add_middleware(RequestIdMiddleware)

# CORS — restricted origins in production
if settings.app_env == "development":
    cors_origins = ["http://localhost:3000", "http://localhost:5173"]
else:
    cors_origins = ["https://app.regulatorai.com"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Routes
app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(search.router, prefix="/api/v1/search", tags=["Search"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
