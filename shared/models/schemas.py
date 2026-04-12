"""Shared Pydantic models used across all services."""
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


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
    email: str
    full_name: str
    role: UserRole = UserRole.ANALYST
    organization: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase, TimestampMixin):
    id: UUID
    is_active: bool = True

    class Config:
        from_attributes = True


# ── Document Models ────────────────────────────────────────

class RegulatoryDocumentBase(BaseModel):
    title: str
    content: str
    url: Optional[str] = None
    jurisdiction: Optional[str] = None
    document_type: Optional[str] = None
    language: str = "en"


class RegulatoryDocumentCreate(RegulatoryDocumentBase):
    source_id: Optional[UUID] = None
    external_id: Optional[str] = None
    published_at: Optional[datetime] = None
    raw_metadata: dict = {}


class RegulatoryDocumentResponse(RegulatoryDocumentBase, TimestampMixin):
    id: UUID
    source_id: Optional[UUID] = None
    content_hash: str
    status: DocumentStatus = DocumentStatus.INGESTED
    raw_metadata: dict = {}

    class Config:
        from_attributes = True


# ── Enrichment Models ──────────────────────────────────────

class ImpactScore(BaseModel):
    region: str
    product_category: str
    score: int = Field(ge=1, le=10)
    justification: str


class KeyChange(BaseModel):
    change: str
    affected_parties: list[str] = []
    effective_date: Optional[str] = None


class Classification(BaseModel):
    domain: str
    confidence: float = Field(ge=0.0, le=1.0)
    sub_categories: list[str] = []


class DocumentEnrichmentCreate(BaseModel):
    document_id: UUID
    summary: Optional[str] = None
    key_changes: list[KeyChange] = []
    classification: list[Classification] = []
    impact_scores: list[ImpactScore] = []
    draft_response: Optional[str] = None
    affected_entities: list[str] = []
    effective_dates: list[str] = []
    urgency_level: UrgencyLevel = UrgencyLevel.NORMAL
    confidence_score: float = 0.0
    token_usage: dict = {}
    processing_time_ms: Optional[int] = None


class DocumentEnrichmentResponse(DocumentEnrichmentCreate, TimestampMixin):
    id: UUID
    agent_version: Optional[str] = None

    class Config:
        from_attributes = True


# ── Search Models ──────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str
    jurisdiction: Optional[str] = None
    category: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    urgency_level: Optional[UrgencyLevel] = None
    search_type: str = "hybrid"  # keyword, semantic, hybrid
    page: int = 1
    page_size: int = 20


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
    title: str
    document_ids: list[UUID]
    report_type: str = "standard"
    template_id: Optional[str] = None


class ComplianceReportResponse(ComplianceReportCreate, TimestampMixin):
    id: UUID
    created_by: Optional[UUID] = None
    content: dict = {}
    file_url: Optional[str] = None
    file_format: str = "pdf"
    status: ReportStatus = ReportStatus.DRAFT

    class Config:
        from_attributes = True


# ── Watch Rule Models ──────────────────────────────────────

class WatchRuleCondition(BaseModel):
    field: str  # jurisdiction, category, keyword, urgency
    operator: str  # equals, contains, gte, lte
    value: str


class WatchRuleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    conditions: list[WatchRuleCondition]
    channels: list[str] = ["email"]


class WatchRuleResponse(WatchRuleCreate, TimestampMixin):
    id: UUID
    user_id: UUID
    is_active: bool = True
    last_triggered_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Event Models (for Redis Pub/Sub) ──────────────────────

class DocumentEvent(BaseModel):
    event_type: str  # document.ingested, document.enriched, document.failed
    document_id: UUID
    metadata: dict = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ── Auth Models ────────────────────────────────────────────

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: str
    password: str
