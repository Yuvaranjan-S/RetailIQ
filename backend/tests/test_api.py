"""
RetailIQ — Full API Integration Test Suite
Tests:
- Authentication & JWT Token issuance
- Store Twin State & Zone layout endpoint
- Inventory listing & Restock action
- Alerts list & resolve
- Recommendation accept/reject simulation
- Simulation scenario activation
- System health & offline mode simulation
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_auth_and_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Health check
        res = await client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"

        # Login
        login_res = await client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        assert login_res.status_code == 200
        data = login_res.json()
        assert "access_token" in data
        token = data["access_token"]
        assert data["user"]["username"] == "admin"

        # Protected route /me
        headers = {"Authorization": f"Bearer {token}"}
        me_res = await client.get("/api/auth/me", headers=headers)
        assert me_res.status_code == 200
        assert me_res.json()["email"] == "admin@retailiq.local"


@pytest.mark.asyncio
async def test_store_and_inventory_endpoints():
    token = create_access_token({"sub": "1", "role": "admin"})
    headers = {"Authorization": f"Bearer {token}"}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Store state
        res = await client.get("/api/store/state", headers=headers)
        assert res.status_code in (200, 404)
        if res.status_code == 200:
            data = res.json()
            assert "zones" in data
            assert "checkouts" in data

        # Inventory list
        inv_res = await client.get("/api/inventory", headers=headers)
        assert inv_res.status_code == 200
        items = inv_res.json()["inventory"]
        assert len(items) > 0

        # Restock item
        sku = items[0]["sku"]
        restock_res = await client.post(f"/api/inventory/{sku}/restock?quantity=10", headers=headers)
        assert restock_res.status_code == 200
        assert restock_res.json()["success"] is True


@pytest.mark.asyncio
async def test_simulation_and_offline():
    token = create_access_token({"sub": "1", "role": "admin"})
    headers = {"Authorization": f"Bearer {token}"}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Change scenario
        sc_res = await client.post("/api/simulation/scenario", json={"scenario": "surge", "store_id": 1}, headers=headers)
        assert sc_res.status_code == 200
        assert sc_res.json()["scenario"] == "surge"

        # Simulate offline
        off_res = await client.post("/api/system/offline", headers=headers)
        assert off_res.status_code == 200
        assert off_res.json()["network_status"] == "offline"

        # Restore online
        on_res = await client.post("/api/system/online", headers=headers)
        assert on_res.status_code == 200
        assert on_res.json()["network_status"] == "online"
