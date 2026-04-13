"""
Factory Boy factories for RegulatorAI ORM models.

Usage:
    from shared.factories import UserFactory, RegulatoryDocumentFactory

    # Create with defaults
    user = UserFactory.build()

    # Override fields
    admin = UserFactory.build(role="admin", email="admin@test.com")

    # Create batch
    users = UserFactory.build_batch(10)

Note: Use .build() for in-memory instances (no DB), .create() for DB-persisted
instances (requires a configured SQLAlchemy session via the factory Meta.sqlalchemy_session).
"""
import hashlib
import uuid
from datetime import datetime, timedelta, timezone

import factory

from shared.models.orm import (
    ComplianceReport,
    DocumentEnrichment,
    RegulatoryDocument,
    RegulatorySource,
    User,
)


def _utcnow():
    return datetime.now(timezone.utc)


# ── User Factory ──────────────────────────────────────────


class UserFactory(factory.Factory):
    """Factory for User model."""

    class Meta:
        model = User

    id = factory.LazyFunction(uuid.uuid4)
    email = factory.Sequence(lambda n: f"user-{n}@regulatorai-test.com")
    password_hash = factory.LazyAttribute(
        lambda _: "$2b$12$LJ3m4ys3Lk0TlNPDv1IMnuD1B3O5eSzFK9mnMRcw8oXZKqSTqWHji"
    )  # bcrypt hash of "TestPass1"
    full_name = factory.Faker("name")
    role = "analyst"
    organization = factory.Faker("company")
    is_active = True
    created_at = factory.LazyFunction(_utcnow)
    updated_at = factory.LazyFunction(_utcnow)


# ── Regulatory Source Factory ─────────────────────────────


class RegulatorySourceFactory(factory.Factory):
    """Factory for RegulatorySource model."""

    class Meta:
        model = RegulatorySource

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Sequence(lambda n: f"Test Source {n}")
    source_type = factory.Iterator(["rss", "api", "crawler", "manual"])
    url = factory.Sequence(lambda n: f"https://source-{n}.regulatorai-test.com/feed")
    jurisdiction = factory.Iterator(["EU", "US-Federal", "UK", "Canada", "APAC"])
    category = factory.Iterator(["privacy", "safety", "finance", "health"])
    crawl_frequency_minutes = 60
    is_active = True
    last_crawled_at = factory.LazyFunction(_utcnow)
    created_at = factory.LazyFunction(_utcnow)


# ── Regulatory Document Factory ──────────────────────────


class RegulatoryDocumentFactory(factory.Factory):
    """Factory for RegulatoryDocument model."""

    class Meta:
        model = RegulatoryDocument

    id = factory.LazyFunction(uuid.uuid4)
    source_id = factory.LazyFunction(uuid.uuid4)
    external_id = factory.Sequence(lambda n: f"EXT-{n:06d}")
    title = factory.Sequence(lambda n: f"Test Regulation Document {n}")
    content = factory.Faker("text", max_nb_chars=2000)
    content_hash = factory.LazyAttribute(
        lambda o: hashlib.sha256(o.content.encode("utf-8")).hexdigest()
    )
    url = factory.Sequence(lambda n: f"https://regulations.test.com/doc/{n}")
    published_at = factory.LazyFunction(
        lambda: _utcnow() - timedelta(days=30)
    )
    jurisdiction = factory.Iterator(["EU", "US-Federal", "UK", "Canada", "APAC"])
    document_type = factory.Iterator(["regulation", "directive", "guidance", "framework"])
    language = "en"
    raw_metadata = factory.LazyFunction(dict)
    status = "ingested"
    created_at = factory.LazyFunction(_utcnow)
    updated_at = factory.LazyFunction(_utcnow)


# ── Document Enrichment Factory ──────────────────────────


class DocumentEnrichmentFactory(factory.Factory):
    """Factory for DocumentEnrichment model."""

    class Meta:
        model = DocumentEnrichment

    id = factory.LazyFunction(uuid.uuid4)
    document_id = factory.LazyFunction(uuid.uuid4)
    summary = factory.Faker("paragraph", nb_sentences=3)
    key_changes = factory.LazyFunction(
        lambda: [
            {"change": "New compliance requirement", "affected_parties": ["AI developers"]},
            {"change": "Updated reporting deadline", "affected_parties": ["Regulators"]},
        ]
    )
    classification = factory.LazyFunction(
        lambda: [
            {"domain": "privacy", "confidence": 0.92},
            {"domain": "safety", "confidence": 0.78},
        ]
    )
    impact_scores = factory.LazyFunction(
        lambda: [
            {"region": "EU", "product_category": "SaaS", "score": 8, "justification": "Direct regulatory impact"},
        ]
    )
    draft_response = factory.Faker("paragraph", nb_sentences=5)
    affected_entities = factory.LazyFunction(lambda: ["AI developers", "Cloud providers"])
    effective_dates = factory.LazyFunction(lambda: ["2025-06-01"])
    urgency_level = factory.Iterator(["low", "normal", "high", "critical"])
    confidence_score = factory.Faker("pyfloat", min_value=0.5, max_value=1.0, right_digits=2)
    token_usage = factory.LazyFunction(lambda: {"prompt_tokens": 1500, "completion_tokens": 800})
    processing_time_ms = factory.Faker("random_int", min=500, max=5000)
    agent_version = "v1.0.0"
    created_at = factory.LazyFunction(_utcnow)
    updated_at = factory.LazyFunction(_utcnow)


# ── Compliance Report Factory ────────────────────────────


class ComplianceReportFactory(factory.Factory):
    """Factory for ComplianceReport model."""

    class Meta:
        model = ComplianceReport

    id = factory.LazyFunction(uuid.uuid4)
    title = factory.Sequence(lambda n: f"Compliance Report {n}")
    created_by = factory.LazyFunction(uuid.uuid4)
    document_ids = factory.LazyFunction(lambda: [str(uuid.uuid4()) for _ in range(3)])
    report_type = factory.Iterator(["standard", "executive", "detailed"])
    template_id = factory.LazyAttribute(lambda o: f"tpl-{o.report_type}")
    content = factory.LazyFunction(
        lambda: {"sections": [{"title": "Summary", "body": "Test report content."}]}
    )
    file_url = None
    file_format = "pdf"
    status = "draft"
    created_at = factory.LazyFunction(_utcnow)
    updated_at = factory.LazyFunction(_utcnow)
