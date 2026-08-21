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

        # Admin system health check
        sys_resp = await client.get("/api/system/health?initData=mock_admin")
        assert sys_resp.status == 200
        sys_data = await sys_resp.json()
        assert sys_data["success"] is True
        assert sys_data["health"]["api_status"] == "ONLINE"

    @pytest.mark.asyncio
    async def test_user_session_and_registration(self, client):
        # 1. New user session -> DRAFT
        resp = await client.get("/api/session?initData=mock_user_1001")
        assert resp.status == 200
        data = await resp.json()
        assert data["success"] is True
        assert data["user_status"] == "DRAFT"
        assert data["user"]["balance"] == 0.0

        # Underage rejection
        underage_resp = await client.post("/api/register?initData=mock_user_1001", json={
            "name": "Ali", "age": 16, "city": "Toshkent", "photo": "data:image/jpeg;base64,mock", "bio": "Hello", "terms_accepted": True
        })
        assert underage_resp.status == 400

        # Valid registration
        reg_resp = await client.post("/api/register?initData=mock_user_1001", json={
            "name": "Ali", "age": 22, "city": "Toshkent", "photo": "data:image/jpeg;base64,mock", "bio": "Kompyuter o'yinlari", "interests": ["🎮 Gaming"], "terms_accepted": True, "language": "uz"
        })
        assert reg_resp.status == 200
        reg_data = await reg_resp.json()
        assert reg_data["user_status"] == "PENDING_APPROVAL"

    @pytest.mark.asyncio
    async def test_notifications_and_tickets(self, client):
        # User session
        await client.get("/api/session?initData=mock_user_2001")
        
        # Check notifications
        notif_resp = await client.get("/api/notifications?initData=mock_user_2001")
        assert notif_resp.status == 200
        notif_data = await notif_resp.json()
        assert notif_data["success"] is True
        assert len(notif_data["notifications"]) >= 1 # Welcome notification

        # Mark read
        read_resp = await client.post("/api/notifications/read?initData=mock_user_2001", json={})
        assert read_resp.status == 200

        # Create support ticket
        ticket_resp = await client.post("/api/tickets/create?initData=mock_user_2001", json={
            "subject": "To'lov haqida savol",
            "category": "Billing",
            "message": "Bonus ballarni qanday ishlatish mumkin?"
        })
        assert ticket_resp.status == 200
        ticket_id = (await ticket_resp.json())["ticket_id"]

        # Admin replies to ticket
        adm_reply = await client.post("/api/admin/ticket/reply?initData=mock_admin", json={
            "ticket_id": ticket_id,
            "text": "Bonus ballar profil faolligi orqali to'planadi."
        })
        assert adm_reply.status == 200

        # User views tickets
        t_list = await client.get("/api/tickets?initData=mock_user_2001")
        t_data = await t_list.json()
        assert t_data["tickets"][0]["status"] == "ANSWERED"
        assert len(t_data["tickets"][0]["messages"]) == 2

    @pytest.mark.asyncio
    async def test_dating_swipes_and_chat(self, client):
        # Register User A
        await client.get("/api/session?initData=mock_user_3001")
        await client.post("/api/register?initData=mock_user_3001", json={
            "name": "Anvar", "age": 24, "city": "Samarqand", "photo": "data:image/jpeg;base64,mock", "bio": "Sayr qilish", "terms_accepted": True
        })
        # Register User B
        await client.get("/api/session?initData=mock_user_3002")
        await client.post("/api/register?initData=mock_user_3002", json={
            "name": "Laylo", "age": 21, "city": "Samarqand", "photo": "data:image/jpeg;base64,mock", "bio": "Musiqa", "terms_accepted": True
        })

        # Admin approves both
        p_list = await (await client.get("/api/admin/pending?initData=mock_admin")).json()
        for u in p_list["users"]:
            await client.post("/api/admin/approve?initData=mock_admin", json={"user_id": u["id"]})

        # User A swipes User B
        u_b = [u for u in p_list["users"] if u["name"] == "Laylo"][0]
        u_a = [u for u in p_list["users"] if u["name"] == "Anvar"][0]

        swipe1 = await client.post("/api/swipe?initData=mock_user_3001", json={"target_id": u_b["id"], "is_like": True})
        assert (await swipe1.json())["match"] is False

        # User B swipes User A -> MATCH!
        swipe2 = await client.post("/api/swipe?initData=mock_user_3002", json={"target_id": u_a["id"], "is_like": True})
        s2_data = await swipe2.json()
        assert s2_data["match"] is True
        match_id = s2_data["match_id"]

        # Send chat message
        msg_resp = await client.post("/api/chat/send?initData=mock_user_3001", json={
            "match_id": match_id,
            "text": "Salom Laylo!"
        })
        assert msg_resp.status == 200

        # View messages
        msgs = await (await client.get(f"/api/chat/messages?match_id={match_id}&initData=mock_user_3002")).json()
        assert len(msgs["messages"]) == 2 # System celebration + user message

    @pytest.mark.asyncio
    async def test_admin_rbac_and_broadcast(self, client):
        # Create user
        await client.get("/api/session?initData=mock_user_8001")
        # Non-admin forbidden on admin routes
        forbidden = await client.get("/api/admin/stats?initData=mock_user_9999")
        assert forbidden.status == 403

        # Admin broadcast
        broadcast_resp = await client.post("/api/admin/broadcast?initData=mock_admin", json={
            "title": "Yangilik 🚀",
            "body": "Barcha foydalanuvchilarga xushxabar!"
        })
        assert broadcast_resp.status == 200
        b_data = await broadcast_resp.json()
        assert b_data["success"] is True
        assert b_data["sent_count"] >= 1

        # Check audit logs
        logs_resp = await client.get("/api/admin/audit-logs?initData=mock_admin")
        assert logs_resp.status == 200
        logs_data = await logs_resp.json()
        assert len(logs_data["logs"]) >= 1
