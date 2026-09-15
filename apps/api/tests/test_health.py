"""Phase 1 tests: health, version, request ID, response envelope."""

import pytest


# ── Liveness check: /health ──────────────────────────────────────────────────


class TestLivenessCheck:
    """Root /health — infrastructure liveness probe."""

    async def test_returns_200(self, client):
        r = await client.get("/health")
        assert r.status_code == 200

    async def test_database_connected(self, client):
        data = (await client.get("/health")).json()
        assert data["data"]["status"] == "healthy"
        assert data["data"]["database"] == "connected"

    async def test_envelope_shape(self, client):
        data = (await client.get("/health")).json()
        assert data["success"] is True
        assert data["error"] is None
        assert isinstance(data["meta"], dict)


# ── API health: /api/v1/health ───────────────────────────────────────────────


class TestApiHealth:
    """Application-level API health — /api/v1/health."""

    async def test_returns_200(self, client):
        r = await client.get("/api/v1/health")
        assert r.status_code == 200

    async def test_includes_environment(self, client):
        data = (await client.get("/api/v1/health")).json()
        assert "environment" in data["data"]

    async def test_database_connected(self, client):
        data = (await client.get("/api/v1/health")).json()
        assert data["data"]["database"] == "connected"

    async def test_envelope_shape(self, client):
        data = (await client.get("/api/v1/health")).json()
        assert data["success"] is True
        assert data["error"] is None
        assert isinstance(data["meta"], dict)


# ── Version: /api/v1/version ─────────────────────────────────────────────────


class TestVersion:
    """Version endpoint — /api/v1/version."""

    async def test_returns_200(self, client):
        r = await client.get("/api/v1/version")
        assert r.status_code == 200

    async def test_contains_required_fields(self, client):
        data = (await client.get("/api/v1/version")).json()
        assert data["data"]["name"] == "AI Habitat"
        assert data["data"]["version"] == "0.1.0"
        assert "environment" in data["data"]

    async def test_envelope_shape(self, client):
        data = (await client.get("/api/v1/version")).json()
        assert data["success"] is True
        assert data["error"] is None


# ── Request ID ───────────────────────────────────────────────────────────────


class TestRequestId:
    """X-Request-ID middleware behaviour."""

    async def test_generates_request_id(self, client):
        r = await client.get("/health")
        rid = r.headers.get("x-request-id")
        assert rid is not None
        assert len(rid) > 0

    async def test_preserves_client_request_id(self, client):
        custom = "test-req-abc-123"
        r = await client.get("/health", headers={"X-Request-ID": custom})
        assert r.headers.get("x-request-id") == custom

    async def test_unique_across_requests(self, client):
        r1 = await client.get("/health")
        r2 = await client.get("/health")
        assert r1.headers["x-request-id"] != r2.headers["x-request-id"]

    async def test_present_on_api_routes(self, client):
        r = await client.get("/api/v1/version")
        assert r.headers.get("x-request-id") is not None


# ── Response envelope ────────────────────────────────────────────────────────


class TestResponseEnvelope:
    """Every API response uses the {success, data, error, meta} envelope."""

    async def test_success_structure(self, client):
        data = (await client.get("/api/v1/version")).json()
        assert set(data.keys()) == {"success", "data", "error", "meta"}
        assert data["success"] is True
        assert data["data"] is not None
        assert data["error"] is None

    async def test_not_found_uses_envelope(self, client):
        r = await client.get("/api/v1/this-does-not-exist")
        assert r.status_code == 404
        body = r.json()
        assert body["success"] is False
        assert body["error"]["code"] == "NOT_FOUND"
        assert body["data"] is None


# ── F-003: Liveness /health — DB unavailable ─────────────────────────────────


class TestLivenessCheckDbFailure:
    """Root /health when database is unavailable → HTTP 503."""

    async def test_returns_503(self, client_db_unavailable):
        r = await client_db_unavailable.get("/health")
        assert r.status_code == 503

    async def test_reports_unhealthy(self, client_db_unavailable):
        data = (await client_db_unavailable.get("/health")).json()
        assert data["success"] is False
        assert data["data"]["status"] == "unhealthy"
        assert data["data"]["database"] == "disconnected"

    async def test_error_code(self, client_db_unavailable):
        data = (await client_db_unavailable.get("/health")).json()
        assert data["error"]["code"] == "DATABASE_UNAVAILABLE"
        assert data["error"]["message"] == "Database is unavailable."

    async def test_envelope_valid_on_503(self, client_db_unavailable):
        data = (await client_db_unavailable.get("/health")).json()
        assert set(data.keys()) == {"success", "data", "error", "meta"}

    async def test_request_id_on_503(self, client_db_unavailable):
        r = await client_db_unavailable.get("/health")
        assert r.headers.get("x-request-id") is not None
        assert len(r.headers["x-request-id"]) > 0


# ── F-003: API /api/v1/health — DB unavailable ──────────────────────────────


class TestApiHealthDbFailure:
    """API /api/v1/health when database is unavailable → HTTP 503."""

    async def test_returns_503(self, client_db_unavailable):
        r = await client_db_unavailable.get("/api/v1/health")
        assert r.status_code == 503

    async def test_reports_unhealthy(self, client_db_unavailable):
        data = (await client_db_unavailable.get("/api/v1/health")).json()
        assert data["success"] is False
        assert data["data"]["status"] == "unhealthy"
        assert data["data"]["database"] == "disconnected"

    async def test_error_code(self, client_db_unavailable):
        data = (await client_db_unavailable.get("/api/v1/health")).json()
        assert data["error"]["code"] == "DATABASE_UNAVAILABLE"

    async def test_request_id_on_503(self, client_db_unavailable):
        r = await client_db_unavailable.get("/api/v1/health")
        assert r.headers.get("x-request-id") is not None
