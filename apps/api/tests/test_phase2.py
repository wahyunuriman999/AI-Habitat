import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.models.user import User
from app.models.habitat import Habitat
from app.models.membership import HabitatMembership
from app.models.ai_identity import AIIdentity
from app.models.participation import HabitatParticipation

@pytest.fixture
async def user_a(client: AsyncClient):
    resp = await client.post("/api/v1/users")
    assert resp.status_code == 201
    user_id = resp.json()["data"]["id"]
    return {"X-User-ID": user_id}, user_id

@pytest.fixture
async def user_b(client: AsyncClient):
    resp = await client.post("/api/v1/users")
    assert resp.status_code == 201
    user_id = resp.json()["data"]["id"]
    return {"X-User-ID": user_id}, user_id


class TestPhase2Matrix:
    """14 Explicit Architectural Test Paths for Phase 2 Verification Gate."""

    async def test_01_identity_independence(self, client: AsyncClient, user_a):
        """I-01: Successfully create an AIIdentity without providing a Habitat ID."""
        headers, _ = user_a
        resp = await client.post("/api/v1/ai-identities", json={"name": "Ada"}, headers=headers)
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["name"] == "Ada"
        assert data["state"] == "ACTIVE"
        assert "habitat_id" not in data

    async def test_02_stewardship(self, client: AsyncClient, user_a, user_b):
        """I-05: User A creates Ada. User A can archive Ada. User B attempts to archive Ada and receives 404."""
        headers_a, _ = user_a
        headers_b, _ = user_b
        
        resp = await client.post("/api/v1/ai-identities", json={"name": "Ada"}, headers=headers_a)
        ada_id = resp.json()["data"]["id"]
        
        # User B attempts to archive
        resp_b = await client.patch(f"/api/v1/ai-identities/{ada_id}", json={"state": "ARCHIVED"}, headers=headers_b)
        assert resp_b.status_code == 404
        
        # User A archives successfully
        resp_a = await client.patch(f"/api/v1/ai-identities/{ada_id}", json={"state": "ARCHIVED"}, headers=headers_a)
        assert resp_a.status_code == 200

    async def test_03_owner_authority_participation(self, client: AsyncClient, user_a, user_b, test_session: AsyncSession):
        """I-06: User A (OWNER) adds Ada to Habitat. User B (MEMBER) attempts to add Bob to Habitat and receives 403."""
        headers_a, user_a_id = user_a
        headers_b, user_b_id = user_b
        
        resp = await client.post("/api/v1/habitats", json={"name": "Lab"}, headers=headers_a)
        lab_id = resp.json()["data"]["id"]
        
        resp_ada = await client.post("/api/v1/ai-identities", json={"name": "Ada"}, headers=headers_a)
        ada_id = resp_ada.json()["data"]["id"]
        
        # Add User B as MEMBER
        membership = HabitatMembership(user_id=uuid.UUID(user_b_id), habitat_id=uuid.UUID(lab_id), role="MEMBER")
        test_session.add(membership)
        await test_session.commit()
        
        # User B tries to add Ada -> 403
        resp_b = await client.post(f"/api/v1/habitats/{lab_id}/participations", json={"ai_identity_id": ada_id}, headers=headers_b)
        assert resp_b.status_code == 403
        
        # User A tries to add Ada -> 201
        resp_a = await client.post(f"/api/v1/habitats/{lab_id}/participations", json={"ai_identity_id": ada_id}, headers=headers_a)
        assert resp_a.status_code == 201

    async def test_04_habitat_isolation(self, client: AsyncClient, user_a, user_b):
        """I-04: User C attempts to view a Habitat they are not a member of and receives 404."""
        headers_a, _ = user_a
        headers_b, _ = user_b
        
        resp = await client.post("/api/v1/habitats", json={"name": "Lab"}, headers=headers_a)
        lab_id = resp.json()["data"]["id"]
        
        resp_b = await client.get(f"/api/v1/habitats/{lab_id}", headers=headers_b)
        assert resp_b.status_code == 404

    async def test_05_archiving_preserves_row(self, client: AsyncClient, user_a, test_session: AsyncSession):
        """I-08: Archiving an AIIdentity updates state="ARCHIVED" but does not remove the database row."""
        headers_a, _ = user_a
        
        resp = await client.post("/api/v1/ai-identities", json={"name": "Ada"}, headers=headers_a)
        ada_id = resp.json()["data"]["id"]
        
        await client.patch(f"/api/v1/ai-identities/{ada_id}", json={"state": "ARCHIVED"}, headers=headers_a)
        
        # Row must exist in DB with state=ARCHIVED
        ada = await test_session.get(AIIdentity, uuid.UUID(ada_id))
        assert ada is not None
        assert ada.state == "ARCHIVED"

    async def test_06_bootstrap(self, client: AsyncClient):
        """P2-C01: POST /api/v1/users successfully creates a User without providing an X-User-ID header."""
        resp = await client.post("/api/v1/users")
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert "id" in data
        assert data["state"] == "ACTIVE"

    async def test_07_atomic_habitat_genesis(self, client: AsyncClient, user_a, test_session: AsyncSession):
        """P2-C05: If Habitat creation fails during the membership step, the Habitat MUST NOT remain persisted."""
        headers_a, user_id = user_a
        
        from unittest.mock import patch
        
        # Mock membership creation to raise an exception, simulating a failure in the transaction
        with patch('app.api.v1.habitats.HabitatMembership') as MockMembership:
            MockMembership.side_effect = Exception("Simulated DB Failure")
            
            with pytest.raises(Exception, match="Simulated DB Failure"):
                await client.post("/api/v1/habitats", json={"name": "FailedLab"}, headers=headers_a)
            
        # Verify rollback occurred (Habitat row must not exist)
        res = await test_session.execute(text("SELECT count(*) FROM habitats WHERE name = 'FailedLab'"))
        count = res.scalar()
        assert count == 0

    async def test_08_ai_visibility_isolation(self, client: AsyncClient, user_a, user_b):
        """P2-C02: User A creates Ada. User B performs GET Ada and receives 404 NOT_FOUND."""
        headers_a, _ = user_a
        headers_b, _ = user_b
        
        resp = await client.post("/api/v1/ai-identities", json={"name": "Ada"}, headers=headers_a)
        ada_id = resp.json()["data"]["id"]
        
        resp_b = await client.get(f"/api/v1/ai-identities/{ada_id}", headers=headers_b)
        assert resp_b.status_code == 404

    async def test_09_archived_ai_cannot_participate(self, client: AsyncClient, user_a):
        """P2-C03: Ada transitions to ARCHIVED. User attempts to add Ada to a Habitat and receives 409 CONFLICT."""
        headers_a, _ = user_a
        
        resp_hab = await client.post("/api/v1/habitats", json={"name": "Lab"}, headers=headers_a)
        lab_id = resp_hab.json()["data"]["id"]
        
        resp_ada = await client.post("/api/v1/ai-identities", json={"name": "Ada"}, headers=headers_a)
        ada_id = resp_ada.json()["data"]["id"]
        
        await client.patch(f"/api/v1/ai-identities/{ada_id}", json={"state": "ARCHIVED"}, headers=headers_a)
        
        resp = await client.post(f"/api/v1/habitats/{lab_id}/participations", json={"ai_identity_id": ada_id}, headers=headers_a)
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "INVALID_ACTION_STATE"

    async def test_10_patch_boundary(self, client: AsyncClient, user_a, user_b):
        """P2-C04: Attempting to modify created_by_user_id via PATCH is rejected/ignored."""
        headers_a, user_a_id = user_a
        _, user_b_id = user_b
        
        resp = await client.post("/api/v1/ai-identities", json={"name": "Ada"}, headers=headers_a)
        ada_id = resp.json()["data"]["id"]
        
        await client.patch(f"/api/v1/ai-identities/{ada_id}", json={"name": "Ada 2.0", "created_by_user_id": user_b_id}, headers=headers_a)
        
        resp_get = await client.get(f"/api/v1/ai-identities/{ada_id}", headers=headers_a)
        assert resp_get.json()["data"]["created_by_user_id"] == user_a_id

    async def test_11_nested_idor_prevention(self, client: AsyncClient, user_a, user_b):
        """P2-FINAL-01: User C attempts to GET participations in a Habitat they do not belong to and receives 404 NOT_FOUND."""
        headers_a, _ = user_a
        headers_b, _ = user_b
        
        resp = await client.post("/api/v1/habitats", json={"name": "Lab"}, headers=headers_a)
        lab_id = resp.json()["data"]["id"]
        
        resp_b_part = await client.get(f"/api/v1/habitats/{lab_id}/participations", headers=headers_b)
        assert resp_b_part.status_code == 404

    async def test_12_archived_habitat_cannot_accept_participations(self, client: AsyncClient, user_a, test_session: AsyncSession):
        """P2-FINAL-02: User attempts to add an AI to an ARCHIVED Habitat and receives 409 CONFLICT."""
        headers_a, _ = user_a
        
        resp_hab = await client.post("/api/v1/habitats", json={"name": "Lab"}, headers=headers_a)
        lab_id = resp_hab.json()["data"]["id"]
        
        habitat = await test_session.get(Habitat, uuid.UUID(lab_id))
        habitat.state = "ARCHIVED"
        await test_session.commit()
        
        resp_ada = await client.post("/api/v1/ai-identities", json={"name": "Ada"}, headers=headers_a)
        ada_id = resp_ada.json()["data"]["id"]
        
        resp = await client.post(f"/api/v1/habitats/{lab_id}/participations", json={"ai_identity_id": ada_id}, headers=headers_a)
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "INVALID_ACTION_STATE"

    async def test_13_physical_database_constraints(self, test_session: AsyncSession):
        """P2-SEAL-02: Attempting to insert illegal state/role into the DB natively MUST raise an integrity error with CHECK constraint failed."""
        
        async def assert_check_constraint_failure(query: str, params: dict):
            with pytest.raises(IntegrityError) as exc_info:
                await test_session.execute(text(query), params)
                await test_session.commit()
            await test_session.rollback()
            # SQLite explicitly outputs 'CHECK constraint failed'
            assert "CHECK constraint failed" in str(exc_info.value)
            
        user_id = uuid.uuid4().hex
        hab_id = uuid.uuid4().hex
        ai_id = uuid.uuid4().hex
        
        # 1. users.state
        await assert_check_constraint_failure(
            "INSERT INTO users (id, state, created_at) VALUES (:id, :state, CURRENT_TIMESTAMP)",
            {"id": uuid.uuid4().hex, "state": "SUPER_AI_MODE"}
        )
        
        # 2. habitats.state
        await assert_check_constraint_failure(
            "INSERT INTO habitats (id, name, state, created_at, updated_at) VALUES (:id, :name, :state, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            {"id": uuid.uuid4().hex, "name": "Lab", "state": "SUPER_AI_MODE"}
        )
        
        # Setup valid base records for FK dependencies
        await test_session.execute(text("INSERT INTO users (id, state, created_at) VALUES (:id, 'ACTIVE', CURRENT_TIMESTAMP)"), {"id": user_id})
        await test_session.execute(text("INSERT INTO habitats (id, name, state, created_at, updated_at) VALUES (:id, 'Lab', 'ACTIVE', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"), {"id": hab_id})
        await test_session.commit()
        
        # 3. ai_identities.state
        await assert_check_constraint_failure(
            "INSERT INTO ai_identities (id, name, created_by_user_id, state, created_at, updated_at) VALUES (:id, :name, :creator, :state, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            {"id": ai_id, "name": "Ada", "creator": user_id, "state": "SUPER_AI_MODE"}
        )
        
        await test_session.execute(text("INSERT INTO ai_identities (id, name, created_by_user_id, state, created_at, updated_at) VALUES (:id, 'Ada', :creator, 'ACTIVE', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"), {"id": ai_id, "creator": user_id})
        await test_session.commit()
        
        # 4. habitat_memberships.role
        await assert_check_constraint_failure(
            "INSERT INTO habitat_memberships (id, user_id, habitat_id, role, created_at) VALUES (:id, :uid, :hid, :role, CURRENT_TIMESTAMP)",
            {"id": uuid.uuid4().hex, "uid": user_id, "hid": hab_id, "role": "GOD_OWNER"}
        )
        
        # 5. habitat_participations.state
        await assert_check_constraint_failure(
            "INSERT INTO habitat_participations (id, ai_identity_id, habitat_id, state, created_at) VALUES (:id, :ai_id, :hid, :state, CURRENT_TIMESTAMP)",
            {"id": uuid.uuid4().hex, "ai_id": ai_id, "hid": hab_id, "state": "SUPER_AI_MODE"}
        )

    async def test_14_one_way_state_transition(self, client: AsyncClient, user_a):
        """P2-SEAL-02: Ada transitions to ARCHIVED. A subsequent PATCH state=ACTIVE is explicitly rejected."""
        headers_a, _ = user_a
        
        resp = await client.post("/api/v1/ai-identities", json={"name": "Ada"}, headers=headers_a)
        ada_id = resp.json()["data"]["id"]
        
        await client.patch(f"/api/v1/ai-identities/{ada_id}", json={"state": "ARCHIVED"}, headers=headers_a)
        
        resp_restore = await client.patch(f"/api/v1/ai-identities/{ada_id}", json={"state": "ACTIVE"}, headers=headers_a)
        assert resp_restore.status_code == 409
        assert resp_restore.json()["error"]["code"] == "INVALID_ACTION_STATE"
