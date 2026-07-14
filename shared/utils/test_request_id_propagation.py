"""Tests for request-ID propagation and the shared error envelope."""

import re
import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient

from shared.utils.errors import register_exception_handlers
from shared.utils.logging import (
    REQUEST_ID_HEADER,
    RequestIdMiddleware,
    propagation_headers,
)

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
)


def _make_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestIdMiddleware)
    register_exception_handlers(app)

    @app.get("/ok")
    async def ok():
        return {"propagated": propagation_headers()}

    @app.get("/boom")
    async def boom():
        raise ValueError("kaboom: secret detail that must not leak")

    return app


class TestRequestIdPropagation:
    def test_generates_uuid_when_absent(self):
        client = TestClient(_make_app())
        resp = client.get("/ok")
        assert _UUID_RE.match(resp.headers[REQUEST_ID_HEADER])

    def test_honors_valid_incoming_id(self):
        incoming = str(uuid.uuid4())
        client = TestClient(_make_app())
        resp = client.get("/ok", headers={REQUEST_ID_HEADER: incoming})
        assert resp.headers[REQUEST_ID_HEADER] == incoming
        # And the handler sees it for further downstream propagation
        assert resp.json()["propagated"] == {REQUEST_ID_HEADER: incoming}

    def test_rejects_malformed_incoming_id(self):
        client = TestClient(_make_app())
        resp = client.get("/ok", headers={REQUEST_ID_HEADER: "not-a-uuid\r\nX-Evil: 1"})
        returned = resp.headers[REQUEST_ID_HEADER]
        assert _UUID_RE.match(returned)
        assert "Evil" not in returned


class TestErrorEnvelope:
    def test_unhandled_exception_returns_envelope_without_stack_trace(self):
        client = TestClient(_make_app(), raise_server_exceptions=False)
        resp = client.get("/boom")
        assert resp.status_code == 500
        body = resp.json()
        assert body["detail"] == "Internal server error"
        assert _UUID_RE.match(body["request_id"])
        assert "kaboom" not in resp.text
        assert "Traceback" not in resp.text

    def test_envelope_request_id_matches_header(self):
        incoming = str(uuid.uuid4())
        client = TestClient(_make_app(), raise_server_exceptions=False)
        resp = client.get("/boom", headers={REQUEST_ID_HEADER: incoming})
        assert resp.json()["request_id"] == incoming
