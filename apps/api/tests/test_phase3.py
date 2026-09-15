import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

@pytest.fixture
async def user_a(client: AsyncClient):
    resp = await client.post("/api/v1/users")
    user_id = resp.json()["data"]["id"]
    return {"X-User-ID": user_id}, user_id

@pytest.fixture
async def user_b(client: AsyncClient):
    resp = await client.post("/api/v1/users")
    user_id = resp.json()["data"]["id"]
    return {"X-User-ID": user_id}, user_id


class TestPhase3Matrix:
    """6 Explicit Architectural Test Paths for Phase 3 Verification Gate."""

    async def test_01_1_to_n_cardinality(self, client: AsyncClient, user_a):
        """1. Successfully create multiple CognitiveBindings for a single AIIdentity."""
        headers, _ = user_a
        
        resp_ai = await client.post("/api/v1/ai-identities", json={"name": "Ada"}, headers=headers)
        ai_id = resp_ai.json()["data"]["id"]
        
        # Create Binding 1
        resp_b1 = await client.post(f"/api/v1/ai-identities/{ai_id}/bindings", json={
            "provider": "openai",
            "model": "gpt-4",
            "is_default": True
        }, headers=headers)
        assert resp_b1.status_code == 201
        
        # Create Binding 2
        resp_b2 = await client.post(f"/api/v1/ai-identities/{ai_id}/bindings", json={
            "provider": "local",
            "model": "llama-3",
            "is_default": False
        }, headers=headers)
        assert resp_b2.status_code == 201
        
        # List bindings
        resp_list = await client.get(f"/api/v1/ai-identities/{ai_id}/bindings", headers=headers)
        assert resp_list.status_code == 200
        assert len(resp_list.json()["data"]) == 2

    async def test_02_steward_isolation(self, client: AsyncClient, user_a, user_b):
        """2. User B attempts to create a CognitiveBinding for User A's AIIdentity and receives 404 NOT_FOUND."""
        headers_a, _ = user_a
        headers_b, _ = user_b
        
        resp_ai = await client.post("/api/v1/ai-identities", json={"name": "Ada"}, headers=headers_a)
        ai_id = resp_ai.json()["data"]["id"]
        
        resp_b = await client.post(f"/api/v1/ai-identities/{ai_id}/bindings", json={
            "provider": "openai",
            "model": "gpt-4",
        }, headers=headers_b)
        
        assert resp_b.status_code == 404

    async def test_03_i_09_enforcement(self, client: AsyncClient, user_a):
        """3. Attempt to POST .../tick for an AIIdentity that does NOT participate in the Habitat. Expect 403."""
        headers, _ = user_a
        
        # Habitat
        resp_hab = await client.post("/api/v1/habitats", json={"name": "Lab"}, headers=headers)
        hab_id = resp_hab.json()["data"]["id"]
        
        # AI Identity
        resp_ai = await client.post("/api/v1/ai-identities", json={"name": "Ada"}, headers=headers)
        ai_id = resp_ai.json()["data"]["id"]
        
        # Do NOT add AI to Habitat
        
        # Attempt tick
        resp_tick = await client.post(
            f"/api/v1/habitats/{hab_id}/participations/{ai_id}/tick",
            json={"event": "ping", "content": "hello"},
            headers=headers
        )
        assert resp_tick.status_code == 403
        assert "active participation" in resp_tick.json()["error"]["message"]

    async def test_04_i_10_enforcement(self, client: AsyncClient, user_a, test_session: AsyncSession):
        """4. The tick endpoint completes successfully, returning an Intent, but DOES NOT mutate core tables."""
        headers, _ = user_a
        
        resp_hab = await client.post("/api/v1/habitats", json={"name": "Lab"}, headers=headers)
        hab_id = resp_hab.json()["data"]["id"]
        
        resp_ai = await client.post("/api/v1/ai-identities", json={"name": "Ada"}, headers=headers)
        ai_id = resp_ai.json()["data"]["id"]
        
        await client.post(f"/api/v1/habitats/{hab_id}/participations", json={"ai_identity_id": ai_id}, headers=headers)
        
        # Record DB counts
        users_count = (await test_session.execute(text("SELECT count(*) FROM users"))).scalar()
        habs_count = (await test_session.execute(text("SELECT count(*) FROM habitats"))).scalar()
        ai_count = (await test_session.execute(text("SELECT count(*) FROM ai_identities"))).scalar()
        part_count = (await test_session.execute(text("SELECT count(*) FROM habitat_participations"))).scalar()
        
        resp_tick = await client.post(
            f"/api/v1/habitats/{hab_id}/participations/{ai_id}/tick",
            json={"event": "ping", "content": "hello"},
            headers=headers
        )
        assert resp_tick.status_code == 200
        
        # Verify DB counts remain identical
        assert users_count == (await test_session.execute(text("SELECT count(*) FROM users"))).scalar()
        assert habs_count == (await test_session.execute(text("SELECT count(*) FROM habitats"))).scalar()
        assert ai_count == (await test_session.execute(text("SELECT count(*) FROM ai_identities"))).scalar()
        assert part_count == (await test_session.execute(text("SELECT count(*) FROM habitat_participations"))).scalar()

    async def test_05_i_11_enforcement(self, client: AsyncClient, user_a):
        """5. The tick endpoint returns an Intent payload representing data, not execution."""
        headers, _ = user_a
        
        resp_hab = await client.post("/api/v1/habitats", json={"name": "Lab"}, headers=headers)
        hab_id = resp_hab.json()["data"]["id"]
        
        resp_ai = await client.post("/api/v1/ai-identities", json={"name": "Ada"}, headers=headers)
        ai_id = resp_ai.json()["data"]["id"]
        
        await client.post(f"/api/v1/habitats/{hab_id}/participations", json={"ai_identity_id": ai_id}, headers=headers)
        
        resp_tick = await client.post(
            f"/api/v1/habitats/{hab_id}/participations/{ai_id}/tick",
            json={"event": "say_hello", "content": "hello"},
            headers=headers
        )
        assert resp_tick.status_code == 200
        data = resp_tick.json()["data"]
        assert data["intent_type"] == "ACKNOWLEDGE_OBSERVATION"
        assert data["payload"]["processed_event"] == "say_hello"

    async def test_06_binding_swappability(self, client: AsyncClient, user_a):
        """6. Change the is_default flag. Execute tick. Verify the Intent reflects the new binding's provider."""
        headers, _ = user_a
        
        resp_hab = await client.post("/api/v1/habitats", json={"name": "Lab"}, headers=headers)
        hab_id = resp_hab.json()["data"]["id"]
        
        resp_ai = await client.post("/api/v1/ai-identities", json={"name": "Ada"}, headers=headers)
        ai_id = resp_ai.json()["data"]["id"]
        
        await client.post(f"/api/v1/habitats/{hab_id}/participations", json={"ai_identity_id": ai_id}, headers=headers)
        
        # Binding A (Default)
        resp_b1 = await client.post(f"/api/v1/ai-identities/{ai_id}/bindings", json={
            "provider": "openai",
            "model": "gpt-4",
            "is_default": True
        }, headers=headers)
        b1_id = resp_b1.json()["data"]["id"]
        
        # Binding B (Not default)
        resp_b2 = await client.post(f"/api/v1/ai-identities/{ai_id}/bindings", json={
            "provider": "local_llama",
            "model": "llama-3",
            "is_default": False
        }, headers=headers)
        b2_id = resp_b2.json()["data"]["id"]
        
        # Tick with Binding A
        resp_tick_1 = await client.post(f"/api/v1/habitats/{hab_id}/participations/{ai_id}/tick", json={"event": "ping", "content": "ping"}, headers=headers)
        assert resp_tick_1.json()["data"]["provider_used"] == "openai"
        
        # Swap defaults via PATCH
        await client.patch(f"/api/v1/ai-identities/{ai_id}/bindings/{b1_id}", json={"is_default": False}, headers=headers)
        await client.patch(f"/api/v1/ai-identities/{ai_id}/bindings/{b2_id}", json={"is_default": True}, headers=headers)
        
        # Tick with Binding B
        resp_tick_2 = await client.post(f"/api/v1/habitats/{hab_id}/participations/{ai_id}/tick", json={"event": "ping", "content": "ping"}, headers=headers)
        assert resp_tick_2.json()["data"]["provider_used"] == "local_llama"
