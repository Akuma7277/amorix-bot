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

class TestEnterpriseSuite:

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
    async def test_gender_registration_and_filtering(self, client):
        # 1. Register Male user looking for Female
        await client.get("/api/session?initData=mock_user_101")
        reg_male = await client.post("/api/register?initData=mock_user_101", json={
            "name": "Jasur", "age": 25, "gender": "MALE", "target_gender": "FEMALE",
            "city": "Toshkent", "photo": "data:image/jpeg;base64,mock", "bio": "Dasturchi", "terms_accepted": True
        })
        assert reg_male.status == 200
        assert (await reg_male.json())["user"]["gender"] == "MALE"

        # 2. Register Female user looking for Male
        await client.get("/api/session?initData=mock_user_102")
        reg_fem = await client.post("/api/register?initData=mock_user_102", json={
            "name": "Madina", "age": 22, "gender": "FEMALE", "target_gender": "MALE",
            "city": "Toshkent", "photo": "data:image/jpeg;base64,mock", "bio": "Dizayner", "terms_accepted": True
        })
        assert reg_fem.status == 200
        assert (await reg_fem.json())["user"]["gender"] == "FEMALE"

        # Admin approves both
        p_list = await (await client.get("/api/admin/pending?initData=mock_admin")).json()
        for u in p_list["users"]:
            await client.post("/api/admin/approve?initData=mock_admin", json={"user_id": u["id"]})

        # Jasur (Male looking for Female) searches profiles -> Should see Madina
        p_resp = await client.get("/api/profiles?initData=mock_user_101")
        p_data = await p_resp.json()
        assert len(p_data["profiles"]) == 1
        assert p_data["profiles"][0]["name"] == "Madina"
        assert p_data["profiles"][0]["gender"] == "FEMALE"

    @pytest.mark.asyncio
    async def test_likes_received_and_premium_activation(self, client):
        # Setup Male user A and Female user B
        await client.get("/api/session?initData=mock_user_201")
        await client.post("/api/register?initData=mock_user_201", json={
            "name": "Bekzod", "age": 26, "gender": "MALE", "target_gender": "FEMALE",
            "city": "Buxoro", "photo": "data:image/jpeg;base64,mock", "bio": "Sport", "terms_accepted": True
        })
        await client.get("/api/session?initData=mock_user_202")
        await client.post("/api/register?initData=mock_user_202", json={
            "name": "Nigora", "age": 23, "gender": "FEMALE", "target_gender": "MALE",
            "city": "Buxoro", "photo": "data:image/jpeg;base64,mock", "bio": "Sayohat", "terms_accepted": True
        })

        p_list = await (await client.get("/api/admin/pending?initData=mock_admin")).json()
        for u in p_list["users"]:
            await client.post("/api/admin/approve?initData=mock_admin", json={"user_id": u["id"]})

        u_bek = [u for u in p_list["users"] if u["name"] == "Bekzod"][0]
        u_nig = [u for u in p_list["users"] if u["name"] == "Nigora"][0]

        # Bekzod likes Nigora
        await client.post("/api/swipe?initData=mock_user_201", json={"target_id": u_nig["id"], "is_like": True})

        # Nigora checks who liked her (Non-premium -> Blurred)
        l_resp1 = await client.get("/api/likes/received?initData=mock_user_202")
        l_data1 = await l_resp1.json()
        assert l_data1["count"] == 1
        assert l_data1["is_premium"] is False
        assert l_data1["profiles"][0]["blurred"] is True

        # Nigora activates Premium ⭐
        prem_resp = await client.post("/api/premium/activate?initData=mock_user_202")
        assert prem_resp.status == 200
        assert (await prem_resp.json())["is_premium"] is True

        # Nigora checks who liked her (Premium -> Unlocked crystal clear)
        l_resp2 = await client.get("/api/likes/received?initData=mock_user_202")
        l_data2 = await l_resp2.json()
        assert l_data2["is_premium"] is True
        assert l_data2["profiles"][0]["name"] == "Bekzod"
        assert "blurred" not in l_data2["profiles"][0]

    @pytest.mark.asyncio
    async def test_notifications_and_tickets(self, client):
        await client.get("/api/session?initData=mock_user_301")
        
        # Check notifications
        notif_resp = await client.get("/api/notifications?initData=mock_user_301")
        assert notif_resp.status == 200
        notif_data = await notif_resp.json()
        assert len(notif_data["notifications"]) >= 1

        # Mark read
        read_resp = await client.post("/api/notifications/read?initData=mock_user_301", json={})
        assert read_resp.status == 200

        # Create support ticket
        ticket_resp = await client.post("/api/tickets/create?initData=mock_user_301", json={
            "subject": "Premium haqida savol",
            "category": "Billing",
            "message": "Premium imtiyozlari qanday?"
        })
        assert ticket_resp.status == 200
        ticket_id = (await ticket_resp.json())["ticket_id"]

        # Admin replies
        adm_reply = await client.post("/api/admin/ticket/reply?initData=mock_admin", json={
            "ticket_id": ticket_id,
            "text": "Premium orqali sizga like bosganlarni ko'rishingiz mumkin."
        })
        assert adm_reply.status == 200

    @pytest.mark.asyncio
    async def test_admin_rbac_and_broadcast(self, client):
        # Non-admin forbidden
        forbidden = await client.get("/api/admin/stats?initData=mock_user_9999")
        assert forbidden.status == 403

        # Create user
        await client.get("/api/session?initData=mock_user_8001")

        # Admin broadcast
        broadcast_resp = await client.post("/api/admin/broadcast?initData=mock_admin", json={
            "title": "Yangilik 🚀",
            "body": "Premium tizimi ishga tushirildi!"
        })
        assert broadcast_resp.status == 200
        b_data = await broadcast_resp.json()
        assert b_data["success"] is True
        assert b_data["sent_count"] >= 1
