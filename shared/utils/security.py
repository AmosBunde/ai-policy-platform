"""Security utilities: password hashing, JWT tokens, content hashing, input sanitization."""
import hashlib
import re
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt as _bcrypt
from jose import JWTError, jwt

from shared.config.settings import get_settings

settings = get_settings()

# ── JWT Configuration ──────────────────────────────────────

_ALLOWED_ALGORITHMS = ["HS256"]


def _get_jwt_secret() -> str:
    """Load JWT secret from settings, enforce minimum length."""
    secret = settings.jwt_secret
    if not secret or len(secret) < 32:
        raise RuntimeError(
            "JWT_SECRET must be at least 32 characters. "
            "Set it via the JWT_SECRET environment variable."
        )
    return secret


# ── Password Hashing ──────────────────────────────────────

def password_hash(password: str) -> str:
    """Hash a password using bcrypt with 12 rounds."""
    salt = _bcrypt.gensalt(rounds=12)
    return _bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def password_verify(password: str, hashed: str) -> bool:
    """Verify a password against a bcrypt hash (constant-time comparison)."""
    return _bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


# ── Password Strength ─────────────────────────────────────

def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password meets minimum strength requirements.

    Returns (is_valid, message).
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"
    return True, "Password meets requirements"


# ── JWT Token Operations ──────────────────────────────────

def create_access_token(
    user_id: uuid.UUID,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token with user claims."""
    secret = _get_jwt_secret()
    now = datetime.now(timezone.utc)
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, secret, algorithm=_ALLOWED_ALGORITHMS[0])


def create_refresh_token(user_id: uuid.UUID) -> str:
    """Create a JWT refresh token with jti for revocation support."""
    secret = _get_jwt_secret()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + timedelta(days=settings.jwt_refresh_token_expire_days),
    }
    return jwt.encode(payload, secret, algorithm=_ALLOWED_ALGORITHMS[0])


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token.

    Raises JWTError on invalid/expired tokens.
    """
    secret = _get_jwt_secret()
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=_ALLOWED_ALGORITHMS,
            options={"require_exp": True, "require_iat": True},
        )
        return payload
    except JWTError:
        raise


# ── Content Hashing ────────────────────────────────────────

def generate_content_hash(content: str) -> str:
    """Generate a SHA-256 hex digest of the content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


# ── Input Sanitization ─────────────────────────────────────

_DANGEROUS_BLOCK_RE = re.compile(
    r"<\s*(script|iframe|object|embed|form|style|link|meta|base)\b[^>]*>.*?</\s*\1\s*>",
    re.IGNORECASE | re.DOTALL,
)
_DANGEROUS_TAG_RE = re.compile(
    r"<\s*/?\s*(script|iframe|object|embed|form|style|link|meta|base)\b[^>]*>",
    re.IGNORECASE,
)
_EVENT_HANDLER_RE = re.compile(r"\s+on\w+\s*=", re.IGNORECASE)
_JAVASCRIPT_URI_RE = re.compile(r"javascript\s*:", re.IGNORECASE)


def sanitize_input(text: str) -> str:
    """Strip dangerous HTML/JS from user-supplied text, preserving safe markdown."""
    # First remove full blocks (e.g. <script>...</script>)
    text = _DANGEROUS_BLOCK_RE.sub("", text)
    # Then remove any remaining orphaned dangerous tags
    text = _DANGEROUS_TAG_RE.sub("", text)
    text = _EVENT_HANDLER_RE.sub(" ", text)
    text = _JAVASCRIPT_URI_RE.sub("", text)
    return text.strip()
