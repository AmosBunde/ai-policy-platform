"""
Locust load testing for RegulatorAI API Gateway.

Run with:
    locust -f scripts/load_test.py --host http://localhost:8000 \
        --users 100 --spawn-rate 10 --run-time 5m

Profiles:
    - SearchUser (weight 3): 60% search, 20% browse docs, 10% view detail, 10% reports
    - AdminUser  (weight 1): ingestion triggers, user management
"""
import random
import uuid

from locust import HttpUser, between, task


# ── Helpers ───────────────────────────────────────────────

SAMPLE_QUERIES = [
    "AI regulation",
    "data privacy GDPR",
    "algorithmic accountability",
    "EU AI Act compliance",
    "risk management framework",
    "automated decision making",
    "transparency requirements",
    "bias mitigation",
    "model governance",
    "regulatory sandbox",
]

JURISDICTIONS = ["EU", "US-Federal", "UK", "Canada", "APAC", "Singapore"]

SAMPLE_DOC_IDS = [
    "00000000-0000-0000-0000-000000000001",
    "00000000-0000-0000-0000-000000000002",
    "00000000-0000-0000-0000-000000000003",
]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


class _AuthenticatedUser(HttpUser):
    """Base class that authenticates on start and caches the token."""

    abstract = True
    wait_time = between(1, 5)
    _token: str = ""
    _user_id: str = ""

    def on_start(self):
        email = f"loadtest-{uuid.uuid4().hex[:8]}@test.com"
        # Try to register, then login
        self.client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "LoadTest1!Pass",
                "full_name": "Load Test User",
            },
        )
        resp = self.client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "LoadTest1!Pass"},
        )
        if resp.status_code == 200:
            data = resp.json()
            self._token = data.get("access_token", "")

    @property
    def _headers(self) -> dict:
        return _auth_headers(self._token)


# ── SearchUser: primary user profile ─────────────────────

class SearchUser(_AuthenticatedUser):
    """Simulates a typical analyst user: mostly searching and browsing."""

    weight = 3

    @task(6)
    def search_documents(self):
        """Search for regulatory documents (60% of traffic)."""
        query = random.choice(SAMPLE_QUERIES)
        jurisdiction = random.choice([None] + JURISDICTIONS)
        payload = {
            "query": query,
            "search_type": random.choice(["keyword", "semantic", "hybrid"]),
            "page": 1,
            "page_size": 20,
        }
        if jurisdiction:
            payload["jurisdiction"] = jurisdiction

        self.client.post(
            "/api/v1/search",
            json=payload,
            headers=self._headers,
            name="/api/v1/search",
        )

    @task(2)
    def browse_documents(self):
        """Browse document list with pagination (20% of traffic)."""
        page = random.randint(1, 10)
        jurisdiction = random.choice([None] + JURISDICTIONS)
        params = {"page": page, "page_size": 20}
        if jurisdiction:
            params["jurisdiction"] = jurisdiction

        self.client.get(
            "/api/v1/documents",
            params=params,
            headers=self._headers,
            name="/api/v1/documents",
        )

    @task(1)
    def view_document_detail(self):
        """View a specific document (10% of traffic)."""
        doc_id = random.choice(SAMPLE_DOC_IDS)
        self.client.get(
            f"/api/v1/documents/{doc_id}",
            headers=self._headers,
            name="/api/v1/documents/[id]",
        )

    @task(1)
    def generate_report(self):
        """Generate a compliance report (10% of traffic)."""
        num_docs = random.randint(1, 3)
        doc_ids = random.sample(SAMPLE_DOC_IDS, min(num_docs, len(SAMPLE_DOC_IDS)))
        self.client.post(
            "/api/v1/reports",
            json={
                "title": f"Load Test Report {uuid.uuid4().hex[:6]}",
                "document_ids": doc_ids,
                "report_type": random.choice(["standard", "executive", "detailed"]),
            },
            headers=self._headers,
            name="/api/v1/reports",
        )


# ── AdminUser: admin operations ──────────────────────────

class AdminUser(_AuthenticatedUser):
    """Simulates admin operations: user management, source management."""

    weight = 1

    def on_start(self):
        # Admin logs in with a pre-seeded admin account
        resp = self.client.post(
            "/api/v1/auth/login",
            json={"email": "admin@regulatorai.com", "password": "AdminPass1!"},
        )
        if resp.status_code == 200:
            data = resp.json()
            self._token = data.get("access_token", "")

    @task(3)
    def list_users(self):
        """List users (admin only)."""
        self.client.get(
            "/api/v1/users",
            params={"page": 1, "page_size": 20},
            headers=self._headers,
            name="/api/v1/users",
        )

    @task(2)
    def list_reports(self):
        """List all reports."""
        self.client.get(
            "/api/v1/reports",
            params={"page": 1, "page_size": 20},
            headers=self._headers,
            name="/api/v1/reports [list]",
        )

    @task(2)
    def list_documents(self):
        """Browse documents as admin."""
        self.client.get(
            "/api/v1/documents",
            params={"page": 1, "page_size": 50},
            headers=self._headers,
            name="/api/v1/documents [admin]",
        )

    @task(1)
    def health_check(self):
        """Check service health."""
        self.client.get("/health", name="/health")

    @task(1)
    def get_search_facets(self):
        """Get search facets."""
        self.client.get(
            "/api/v1/search/facets",
            headers=self._headers,
            name="/api/v1/search/facets",
        )
