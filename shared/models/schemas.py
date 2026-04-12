"""Shared Pydantic models used across all services."""
import html
import re
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ── HTML Sanitizer ────────────────────────────────────────

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


def sanitize_html(value: str) -> str:
    """Strip dangerous HTML tags and event handlers, preserve safe markdown."""
    value = _DANGEROUS_BLOCK_RE.sub("", value)
    value = _DANGEROUS_TAG_RE.sub("", value)
    value = _EVENT_HANDLER_RE.sub(" ", value)
    value = _JAVASCRIPT_URI_RE.sub("", value)
    return value.strip()


# ── Enums ──────────────────────────────────────────────────

class DocumentStatus(str, Enum):
    INGESTED = "ingested"
    PROCESSING = "processing"
    ENRICHED = "enriched"
    FAILED = "failed"
    ARCHIVED = "archived"


class UrgencyLevel(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class UserRole(str, Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class ReportStatus(str, Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class SourceType(str, Enum):
    RSS = "rss"
    API = "api"
    CRAWLER = "crawler"
    MANUAL = "manual"


# ── Base Models ────────────────────────────────────────────

class TimestampMixin(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ── User Models ────────────────────────────────────────────

class UserBase(BaseModel):
    email: str = Field(..., max_length=255)
    full_name: str = Field(..., max_length=255)
    role: UserRole = UserRole.ANALYST
    organization: Optional[str] = Field(None, max_length=255)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", v):
            raise ValueError("Invalid email format")
        return v

    @field_validator("full_name")
    @classmethod
    def sanitize_full_name(cls, v: str) -> str:
        return sanitize_html(v)

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "email": "analyst@company.com",
                    "full_name": "Jane Doe",
                    "role": "analyst",
                    "organization": "Acme Corp",
                }
            ]
        }
    )


class UserCreate(UserBase):
    model_config = ConfigDict(strict=True)
    password: str = Field(..., min_length=8, max_length=128)


class UserResponse(UserBase, TimestampMixin):
    id: UUID
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


# ── Document Models ────────────────────────────────────────

class RegulatoryDocumentBase(BaseModel):
    title: str = Field(..., max_length=500)
    content: str = Field(..., max_length=1_000_000)
    url: Optional[str] = Field(None, max_length=2048)
    jurisdiction: Optional[str] = Field(None, max_length=100)
    document_type: Optional[str] = Field(None, max_length=50)
    language: str = Field("en", max_length=10)

    @field_validator("title")
    @classmethod
    def sanitize_title(cls, v: str) -> str:
        return sanitize_html(v)

    @field_validator("content")
    @classmethod
    def sanitize_content(cls, v: str) -> str:
        return sanitize_html(v)

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if not re.match(r"^https?://", v):
                raise ValueError("URL must start with http:// or https://")
        return v


class RegulatoryDocumentCreate(RegulatoryDocumentBase):
    source_id: Optional[UUID] = None
    external_id: Optional[str] = Field(None, max_length=255)
    published_at: Optional[datetime] = None
    raw_metadata: dict = {}

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "EU AI Act Final Text",
                    "content": "Full regulation text...",
                    "jurisdiction": "EU",
                    "document_type": "regulation",
                }
            ]
        }
    )


class RegulatoryDocumentResponse(RegulatoryDocumentBase, TimestampMixin):
    id: UUID
    source_id: Optional[UUID] = None
    content_hash: str
    status: DocumentStatus = DocumentStatus.INGESTED
    raw_metadata: dict = {}

    model_config = ConfigDict(from_attributes=True)


# ── Enrichment Models ──────────────────────────────────────

class ImpactScore(BaseModel):
    region: str = Field(..., max_length=100)
    product_category: str = Field(..., max_length=100)
    score: int = Field(ge=1, le=10)
    justification: str = Field(..., max_length=1000)


class KeyChange(BaseModel):
    change: str = Field(..., max_length=2000)
    affected_parties: list[str] = []
    effective_date: Optional[str] = Field(None, max_length=50)


class Classification(BaseModel):
    domain: str = Field(..., max_length=100)
    confidence: float = Field(ge=0.0, le=1.0)
    sub_categories: list[str] = []


class DocumentEnrichmentCreate(BaseModel):
    document_id: UUID
    summary: Optional[str] = Field(None, max_length=10_000)
    key_changes: list[KeyChange] = []
    classification: list[Classification] = []
    impact_scores: list[ImpactScore] = []
    draft_response: Optional[str] = Field(None, max_length=50_000)
    affected_entities: list[str] = []
    effective_dates: list[str] = []
    urgency_level: UrgencyLevel = UrgencyLevel.NORMAL
    confidence_score: float = Field(0.0, ge=0.0, le=1.0)
    token_usage: dict = {}
    processing_time_ms: Optional[int] = Field(None, ge=0)

    @field_validator("summary")
    @classmethod
    def sanitize_summary(cls, v: str | None) -> str | None:
        if v is not None:
            return sanitize_html(v)
        return v


class DocumentEnrichmentResponse(DocumentEnrichmentCreate, TimestampMixin):
    id: UUID
    agent_version: Optional[str] = Field(None, max_length=50)

    model_config = ConfigDict(from_attributes=True)


# ── Search Models ──────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    jurisdiction: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    urgency_level: Optional[UrgencyLevel] = None
    search_type: str = Field("hybrid", pattern=r"^(keyword|semantic|hybrid)$")
    page: int = Field(1, ge=1, le=1000)
    page_size: int = Field(20, ge=1, le=100)


class SearchResult(BaseModel):
    document_id: UUID
    title: str
    snippet: str
    score: float
    jurisdiction: Optional[str] = None
    published_at: Optional[datetime] = None
    urgency_level: Optional[str] = None
    highlights: list[str] = []


class SearchResponse(BaseModel):
    results: list[SearchResult]
    total: int
    page: int
    page_size: int
    query: str


# ── Report Models ──────────────────────────────────────────

class ComplianceReportCreate(BaseModel):
    title: str = Field(..., max_length=500)
    document_ids: list[UUID]
    report_type: str = Field("standard", max_length=50)
    template_id: Optional[str] = Field(None, max_length=100)

    @field_validator("title")
    @classmethod
    def sanitize_report_title(cls, v: str) -> str:
        return sanitize_html(v)


class ComplianceReportResponse(ComplianceReportCreate, TimestampMixin):
    id: UUID
    created_by: Optional[UUID] = None
    content: dict = {}
    file_url: Optional[str] = None
    file_format: str = "pdf"
    status: ReportStatus = ReportStatus.DRAFT

    model_config = ConfigDict(from_attributes=True)


# ── Watch Rule Models ──────────────────────────────────────

class WatchRuleCondition(BaseModel):
    field: str = Field(..., max_length=100)
    operator: str = Field(..., pattern=r"^(equals|contains|gte|lte)$")
    value: str = Field(..., max_length=500)


class WatchRuleCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    conditions: list[WatchRuleCondition]
    channels: list[str] = ["email"]

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        return sanitize_html(v)


class WatchRuleResponse(WatchRuleCreate, TimestampMixin):
    id: UUID
    user_id: UUID
    is_active: bool = True
    last_triggered_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ── Event Models (for Redis Pub/Sub) ──────────────────────

class DocumentEvent(BaseModel):
    event_type: str = Field(..., pattern=r"^document\.(ingested|enriched|failed|archived)$")
    document_id: UUID
    metadata: dict = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ── Auth Models ────────────────────────────────────────────

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    email: str = Field(..., max_length=255)
    password: str = Field(..., max_length=128)
