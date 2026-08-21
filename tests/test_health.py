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

class TestKairyxEnterpriseSuite:

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
        await client.get("/api/session?initData=mock_user_1001")

        status_resp = await client.get("/api/rewards/daily/status?initData=mock_user_1001")
        assert status_resp.status == 200
        s_data = await status_resp.json()
        assert s_data["can_claim"] is True

        claim_resp = await client.post("/api/rewards/daily/claim?initData=mock_user_1001")
        assert claim_resp.status == 200
        c_data = await claim_resp.json()
        assert c_data["streak_days"] == 1
        assert c_data["reward_awarded"]["xp"] == 50

    @pytest.mark.asyncio
    async def test_profile_edit_and_age_validation(self, client):
        # 1. Register user
        await client.get("/api/session?initData=mock_user_5001")
        
        # 2. Update with invalid age (<18) -> Should fail 400
        fail_underage = await client.post("/api/profile/update?initData=mock_user_5001", json={
            "name": "Sarvar",
            "age": 16,
            "city": "Toshkent"
        })
        assert fail_underage.status == 400
        assert (await fail_underage.json())["error"]["code"] == "INVALID_AGE"

        # 3. Update with invalid age (>99) -> Should fail 400
        fail_overage = await client.post("/api/profile/update?initData=mock_user_5001", json={
            "name": "Sarvar",
            "age": 120,
            "city": "Toshkent"
        })
        assert fail_overage.status == 400

        # 4. Update with valid age (22) and new photo -> Should succeed 200
        success_update = await client.post("/api/profile/update?initData=mock_user_5001", json={
            "name": "Sarvar Bek",
            "age": 22,
            "city": "Samarqand",
            "photo": "data:image/jpeg;base64,valid_photo_data_1234567890"
        })
        assert success_update.status == 200
        u_data = (await success_update.json())["user"]
        assert u_data["name"] == "Sarvar Bek"
        assert u_data["age"] == 22
        assert u_data["city"] == "Samarqand"
        assert u_data["photo"] == "data:image/jpeg;base64,valid_photo_data_1234567890"

    @pytest.mark.asyncio
    async def test_vip_photo_deletion_security(self, client):
        # 1. User registers and sets photo
        await client.get("/api/session?initData=mock_user_6001")
        await client.post("/api/profile/update?initData=mock_user_6001", json={
            "name": "Alisher",
            "age": 25,
            "photo": "data:image/jpeg;base64,sample_photo_data_9876543210"
        })

        # 2. Non-VIP tries to delete photo -> Forbidden 403
        del_attempt_free = await client.post("/api/profile/photo/delete?initData=mock_user_6001")
        assert del_attempt_free.status == 403
        assert (await del_attempt_free.json())["error"]["code"] == "VIP_REQUIRED"

        del_via_update_free = await client.post("/api/profile/update?initData=mock_user_6001", json={
            "photo": ""
        })
        assert del_via_update_free.status == 403

        # 3. User submits payment for VIP and Admin approves
        order_resp = await client.post("/api/payment/submit?initData=mock_user_6001", json={
            "plan_tier": "VIP",
            "period": "monthly",
            "amount": 89000.0,
            "receipt_photo": "data:image/jpeg;base64,receipt_data"
        })
        order_id = (await order_resp.json())["order_id"]
        await client.post("/api/admin/payment/approve?initData=mock_admin", json={"order_id": order_id})

        # 4. VIP user now deletes photo -> Succeeds 200
        del_attempt_vip = await client.post("/api/profile/photo/delete?initData=mock_user_6001")
        assert del_attempt_vip.status == 200
        assert (await del_attempt_vip.json())["user"]["photo"] is None

    @pytest.mark.asyncio
    async def test_receipt_payment_checkout_flow(self, client):
        await client.get("/api/session?initData=mock_user_2001")

        order_resp = await client.post("/api/payment/submit?initData=mock_user_2001", json={
            "plan_tier": "VIP",
            "period": "yearly",
            "amount": 710000.0,
            "receipt_photo": "data:image/jpeg;base64,mock_receipt_image_data"
        })
        assert order_resp.status == 200
        order_id = (await order_resp.json())["order_id"]

        adm_payments_resp = await client.get("/api/admin/payments?initData=mock_admin")
        assert adm_payments_resp.status == 200
        adm_data = await adm_payments_resp.json()
        assert len(adm_data["orders"]) >= 1

        approve_resp = await client.post("/api/admin/payment/approve?initData=mock_admin", json={"order_id": order_id})
        assert approve_resp.status == 200

        user_sess = await (await client.get("/api/session?initData=mock_user_2001")).json()
        assert user_sess["user"]["plan_tier"] == "VIP"
        assert user_sess["user"]["is_premium"] is True
