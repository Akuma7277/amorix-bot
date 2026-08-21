import pytest
import pytest_asyncio
import aiohttp
from aiohttp.test_utils import TestClient, TestServer
from webapp.api import create_webapp_app
from models import Base
import engine as engine_module

@pytest_asyncio.fixture
async def client():
    async with engine_module.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    app = create_webapp_app()
    client = TestClient(TestServer(app))
    await client.start_server()
    yield client
    await client.close()

class TestKairyxEnterprisePaymentSuite:

    @pytest.mark.asyncio
    async def test_health_and_system(self, client):
        resp = await client.get("/health")
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "ok"

        ready_resp = await client.get("/health/ready")
        assert ready_resp.status == 200
        ready_data = await ready_resp.json()
        assert ready_data["status"] == "ready"

    @pytest.mark.asyncio
    async def test_daily_streak_and_rewards(self, client):
        # Initialize user
        await client.get("/api/session?initData=mock_user_1001")

        # Check initial streak status
        status_resp = await client.get("/api/rewards/daily/status?initData=mock_user_1001")
        assert status_resp.status == 200
        s_data = await status_resp.json()
        assert s_data["can_claim"] is True

        # Claim Day 1 reward
        claim_resp = await client.post("/api/rewards/daily/claim?initData=mock_user_1001")
        assert claim_resp.status == 200
        c_data = await claim_resp.json()
        assert c_data["streak_days"] == 1
        assert c_data["reward_awarded"]["xp"] == 50

        # Duplicate claim attempt -> Should be rejected
        dup_claim = await client.post("/api/rewards/daily/claim?initData=mock_user_1001")
        assert dup_claim.status == 400

    @pytest.mark.asyncio
    async def test_receipt_payment_checkout_flow(self, client):
        # 1. User registers & visits paywall
        await client.get("/api/session?initData=mock_user_2001")

        # 2. User checks available plans & card
        plans_resp = await client.get("/api/premium/plans?initData=mock_user_2001")
        assert plans_resp.status == 200
        p_data = await plans_resp.json()
        assert p_data["card_number"] == "9860 6004 3347 6527"

        # 3. User submits receipt photo for VIP yearly
        order_resp = await client.post("/api/payment/submit?initData=mock_user_2001", json={
            "plan_tier": "VIP",
            "period": "yearly",
            "amount": 710000.0,
            "receipt_photo": "data:image/jpeg;base64,mock_receipt_image_data"
        })
        assert order_resp.status == 200
        order_data = await order_resp.json()
        order_id = order_data["order_id"]
        assert order_id is not None

        # 4. Admin views pending payments list
        adm_payments_resp = await client.get("/api/admin/payments?initData=mock_admin")
        assert adm_payments_resp.status == 200
        adm_data = await adm_payments_resp.json()
        assert len(adm_data["orders"]) >= 1
        found_order = [o for o in adm_data["orders"] if o["id"] == order_id][0]
        assert found_order["status"] == "PENDING"
        assert found_order["amount"] == 710000.0
        assert found_order["card_number"] == "9860 6004 3347 6527"

        # 5. Admin approves payment -> Obuna activates
        approve_resp = await client.post("/api/admin/payment/approve?initData=mock_admin", json={"order_id": order_id})
        assert approve_resp.status == 200
        assert (await approve_resp.json())["success"] is True

        # 6. User re-verifies session -> Plan is now VIP
        user_sess = await (await client.get("/api/session?initData=mock_user_2001")).json()
        assert user_sess["user"]["plan_tier"] == "VIP"
        assert user_sess["user"]["is_premium"] is True
        assert "👑 VIP" in user_sess["user"]["badges"]

    @pytest.mark.asyncio
    async def test_receipt_payment_rejection(self, client):
        await client.get("/api/session?initData=mock_user_3001")

        order_resp = await client.post("/api/payment/submit?initData=mock_user_3001", json={
            "plan_tier": "PREMIUM",
            "period": "monthly",
            "amount": 49000.0,
            "receipt_photo": "data:image/jpeg;base64,invalid_receipt"
        })
        order_id = (await order_resp.json())["order_id"]

        # Admin rejects
        reject_resp = await client.post("/api/admin/payment/reject?initData=mock_admin", json={
            "order_id": order_id,
            "reason": "Chek fotosi noaniq"
        })
        assert reject_resp.status == 200

        # User remains FREE
        user_sess = await (await client.get("/api/session?initData=mock_user_3001")).json()
        assert user_sess["user"]["plan_tier"] == "FREE"

    @pytest.mark.asyncio
    async def test_coupons_and_referral(self, client):
        await client.get("/api/session?initData=mock_user_4001")
        promo_resp = await client.post("/api/coupons/redeem?initData=mock_user_4001", json={"code": "KAIRYX2026"})
        assert promo_resp.status == 200
        assert (await promo_resp.json())["success"] is True

        ref_resp = await client.get("/api/referral?initData=mock_user_4001")
        assert ref_resp.status == 200
        assert "t.me/Ka1ryx_bot?start=ref_" in (await ref_resp.json())["referral_link"]
