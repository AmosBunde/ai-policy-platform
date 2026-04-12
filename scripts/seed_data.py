"""Idempotent seed script for development data.

Usage:
    python -m scripts.seed_data
"""
import asyncio
import hashlib
import os
import sys

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bcrypt as _bcrypt

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from shared.config.settings import get_settings
from shared.models.orm import (
    RegulatoryDocument,
    RegulatorySource,
    User,
)

settings = get_settings()

# Dev admin password — override via SEED_ADMIN_PASSWORD env var
ADMIN_PASSWORD = os.environ.get("SEED_ADMIN_PASSWORD", "admin123")


def hash_password(password: str) -> str:
    salt = _bcrypt.gensalt(rounds=12)
    return _bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def compute_content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


ADMIN_USER = {
    "email": "admin@regulatorai.com",
    "password_hash": hash_password(ADMIN_PASSWORD),
    "full_name": "System Admin",
    "role": "admin",
    "is_active": True,
}

SOURCES = [
    {
        "name": "EU AI Act Official",
        "source_type": "crawler",
        "url": "https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai",
        "jurisdiction": "EU",
        "category": "ai_regulation",
        "crawl_frequency_minutes": 60,
    },
    {
        "name": "US Federal Register AI",
        "source_type": "api",
        "url": "https://www.federalregister.gov/api/v1/documents",
        "jurisdiction": "US-Federal",
        "category": "ai_regulation",
        "crawl_frequency_minutes": 30,
    },
    {
        "name": "UK ICO AI Guidance",
        "source_type": "crawler",
        "url": "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/artificial-intelligence/",
        "jurisdiction": "UK",
        "category": "data_protection",
        "crawl_frequency_minutes": 120,
    },
    {
        "name": "NIST AI RMF",
        "source_type": "crawler",
        "url": "https://www.nist.gov/artificial-intelligence",
        "jurisdiction": "US-Federal",
        "category": "ai_standards",
        "crawl_frequency_minutes": 120,
    },
]

SAMPLE_DOCUMENTS = [
    {
        "title": "EU AI Act - Final Text (2024)",
        "content": "The EU AI Act establishes a comprehensive regulatory framework for artificial intelligence systems in the European Union. It classifies AI systems by risk level and imposes requirements proportional to that risk.",
        "jurisdiction": "EU",
        "document_type": "regulation",
        "language": "en",
        "status": "enriched",
        "raw_metadata": {"version": "final", "year": 2024},
    },
    {
        "title": "NIST AI Risk Management Framework 1.0",
        "content": "The NIST AI RMF provides a structured approach for managing risks associated with AI systems throughout their lifecycle. It covers governance, mapping, measuring, and managing AI risks.",
        "jurisdiction": "US-Federal",
        "document_type": "framework",
        "language": "en",
        "status": "enriched",
        "raw_metadata": {"version": "1.0", "year": 2023},
    },
    {
        "title": "UK ICO Guidance on AI and Data Protection",
        "content": "The UK Information Commissioner's Office provides guidance on how data protection law applies to AI systems, including requirements for transparency, fairness, and accountability in automated decision-making.",
        "jurisdiction": "UK",
        "document_type": "guidance",
        "language": "en",
        "status": "ingested",
        "raw_metadata": {"authority": "ICO", "year": 2024},
    },
]


async def seed(session: AsyncSession) -> None:
    """Seed the database idempotently."""

    # 1. Admin user
    result = await session.execute(
        select(User).where(User.email == ADMIN_USER["email"])
    )
    if result.scalar_one_or_none() is None:
        session.add(User(**ADMIN_USER))
        print(f"  Created admin user: {ADMIN_USER['email']}")
    else:
        print(f"  Admin user already exists: {ADMIN_USER['email']}")

    await session.flush()

    # 2. Regulatory sources
    for src_data in SOURCES:
        result = await session.execute(
            select(RegulatorySource).where(RegulatorySource.name == src_data["name"])
        )
        if result.scalar_one_or_none() is None:
            session.add(RegulatorySource(**src_data))
            print(f"  Created source: {src_data['name']}")
        else:
            print(f"  Source already exists: {src_data['name']}")

    await session.flush()

    # 3. Sample documents — link to first source
    result = await session.execute(
        select(RegulatorySource).where(RegulatorySource.name == SOURCES[0]["name"])
    )
    first_source = result.scalar_one_or_none()

    for doc_data in SAMPLE_DOCUMENTS:
        content_hash = compute_content_hash(doc_data["content"])
        result = await session.execute(
            select(RegulatoryDocument).where(
                RegulatoryDocument.content_hash == content_hash
            )
        )
        if result.scalar_one_or_none() is None:
            doc = RegulatoryDocument(
                source_id=first_source.id if first_source else None,
                content_hash=content_hash,
                **doc_data,
            )
            session.add(doc)
            print(f"  Created document: {doc_data['title']}")
        else:
            print(f"  Document already exists: {doc_data['title']}")

    await session.commit()
    print("\nSeed complete.")


async def main() -> None:
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    print("Seeding database...")
    async with session_factory() as session:
        await seed(session)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
