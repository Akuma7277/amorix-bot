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

class TestEnterpriseGamificationRetentionSuite:

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

        sys_resp = await client.get("/api/system/health?initData=mock_admin")
        assert sys_resp.status == 200
        sys_data = await sys_resp.json()
        assert sys_data["success"] is True
        assert sys_data["health"]["api_status"] == "ONLINE"

    @pytest.mark.asyncio
    async def test_daily_streak_and_rewards(self, client):
        # Initialize user
        await client.get("/api/session?initData=mock_user_1001")

        # Check initial streak status
        status_resp = await client.get("/api/rewards/daily/status?initData=mock_user_1001")
        assert status_resp.status == 200
        s_data = await status_resp.json()
        assert s_data["can_claim"] is True
        assert len(s_data["rewards_table"]) == 7

        # Claim Day 1 reward
        claim_resp = await client.post("/api/rewards/daily/claim?initData=mock_user_1001")
        assert claim_resp.status == 200
        c_data = await claim_resp.json()
        assert c_data["streak_days"] == 1
        assert c_data["reward_awarded"]["xp"] == 50

        # Attempt duplicate claim on same day -> Should fail
        dup_claim = await client.post("/api/rewards/daily/claim?initData=mock_user_1001")
        assert dup_claim.status == 400
        assert (await dup_claim.json())["error"]["code"] == "ALREADY_CLAIMED"

    @pytest.mark.asyncio
    async def test_missions_and_leaderboard(self, client):
        # Register user with high completion
        await client.get("/api/session?initData=mock_user_2001")
        await client.post("/api/register?initData=mock_user_2001", json={
            "name": "Sardor", "age": 24, "gender": "MALE", "target_gender": "FEMALE",
            "city": "Samarqand", "photo": "data:image/jpeg;base64,mock", "bio": "IT Leader",
            "interests": ["💻 Technology", "🎮 Gaming"], "terms_accepted": True
        })

        # Check daily missions
        m_resp = await client.get("/api/missions?initData=mock_user_2001")
        assert m_resp.status == 200
        m_data = await m_resp.json()
        assert len(m_data["missions"]) >= 3

        # Check leaderboard
        lb_resp = await client.get("/api/leaderboard?initData=mock_user_2001")
        assert lb_resp.status == 200
        lb_data = await lb_resp.json()
        assert "leaderboard" in lb_data

    @pytest.mark.asyncio
    async def test_coupons_and_promo_codes(self, client):
        await client.get("/api/session?initData=mock_user_3001")

        # Redeem valid promo code KAIRYX2026
        promo_resp = await client.post("/api/coupons/redeem?initData=mock_user_3001", json={"code": "KAIRYX2026"})
        assert promo_resp.status == 200
        p_data = await promo_resp.json()
        assert p_data["success"] is True
        assert p_data["user"]["is_premium"] is True

        # Duplicate redemption by same user -> Should fail
        dup_promo = await client.post("/api/coupons/redeem?initData=mock_user_3001", json={"code": "KAIRYX2026"})
        assert dup_promo.status == 400
        assert (await dup_promo.json())["error"]["code"] == "ALREADY_REDEEMED"

    @pytest.mark.asyncio
    async def test_referral_and_anti_fraud(self, client):
        # User A
        sess_a = await (await client.get("/api/session?initData=mock_user_4001")).json()
        user_a_id = sess_a["user"]["id"]

        # User B registers with User A's referral link
        await client.get(f"/api/session?initData=mock_user_4002&start_param=ref_{user_a_id}")
        reg_b = await client.post("/api/register?initData=mock_user_4002", json={
            "name": "Dilnoza", "age": 21, "gender": "FEMALE", "target_gender": "MALE",
            "city": "Farg'ona", "photo": "data:image/jpeg;base64,mock", "bio": "Talaba",
            "interests": ["🎨 Art"], "terms_accepted": True
        })
        assert reg_b.status == 200

        # Verify User A received referral count and XP
        ref_info = await (await client.get("/api/referral?initData=mock_user_4001")).json()
        assert ref_info["referral_count"] == 1
        assert "t.me/Ka1ryx_bot?start=ref_" in ref_info["referral_link"]

    @pytest.mark.asyncio
    async def test_multi_tier_plans_and_vip_features(self, client):
        # User registers
        await client.get("/api/session?initData=mock_user_5001")

        # Get plans table
        plans_resp = await client.get("/api/premium/plans?initData=mock_user_5001")
        assert plans_resp.status == 200
        plans_data = await plans_resp.json()
        assert "FREE" in plans_data["plans"]
        assert "PREMIUM" in plans_data["plans"]
        assert "VIP" in plans_data["plans"]

        # Subscribe to VIP tier
        sub_resp = await client.post("/api/premium/subscribe?initData=mock_user_5001", json={"tier": "VIP", "period": "yearly"})
        assert sub_resp.status == 200
        sub_data = await sub_resp.json()
        assert sub_data["user"]["plan_tier"] == "VIP"
        assert "👑 VIP" in sub_data["user"]["badges"]

    @pytest.mark.asyncio
    async def test_admin_retention_and_control_center(self, client):
        # Fetch retention metrics as admin
        ret_resp = await client.get("/api/admin/retention?initData=mock_admin")
        assert ret_resp.status == 200
        r_data = await ret_resp.json()
        assert "dau" in r_data["metrics"]
        assert "retention_d1_pct" in r_data["metrics"]

        # Broadcast message
        bc_resp = await client.post("/api/admin/broadcast?initData=mock_admin", json={
            "title": "🎉 Yangi 7-Kunlik Bonus!",
            "body": "Har kuni ilovaga kiring va VIP mukofotlarni qo'lga kiriting."
        })
        assert bc_resp.status == 200
        assert (await bc_resp.json())["success"] is True
