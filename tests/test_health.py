import unittest
from aiohttp import web
from webapp.api import create_webapp_app
from aiohttp.test_utils import AioHTTPTestCase

class TestHealthEndpoints(AioHTTPTestCase):
    async def get_application(self):
        return create_webapp_app()

    async def clear_db(self):
        from engine import async_session_maker
        from models import Base
        from sqlalchemy import text
        try:
            async with async_session_maker() as session:
                await session.execute(text("DELETE FROM reports;"))
                await session.execute(text("DELETE FROM blocks;"))
                await session.execute(text("DELETE FROM messages;"))
                await session.execute(text("DELETE FROM matches;"))
                await session.execute(text("DELETE FROM swipes;"))
                await session.execute(text("DELETE FROM users;"))
                await session.commit()
        except Exception as e:
            print("clear_db warning:", e)

    async def test_health_endpoints(self):
        resp = await self.client.get("/health")
        self.assertEqual(resp.status, 200)
        data = await resp.json()
        self.assertEqual(data["status"], "ok")

        resp_ready = await self.client.get("/health/ready")
        self.assertEqual(resp_ready.status, 200)
        data_ready = await resp_ready.json()
        self.assertEqual(data_ready["status"], "ready")

    async def test_session_lifecycle(self):
        await self.clear_db()
        resp = await self.client.get("/api/session")
        self.assertEqual(resp.status, 401)

        resp = await self.client.get("/api/session?initData=mock_user")
        self.assertEqual(resp.status, 200)
        data = await resp.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["user_status"], "DRAFT")

    async def test_registration_and_validation(self):
        await self.clear_db()
        await self.client.get("/api/session?initData=mock_user")

        underage_payload = {
            "name": "Alex", "age": 16, "city": "Tashkent",
            "photo": "photo_data", "bio": "Hello", "terms_accepted": True
        }
        resp = await self.client.post("/api/register?initData=mock_user", json=underage_payload)
        self.assertEqual(resp.status, 400)

        valid_payload = {
            "name": "Alex", "age": 22, "city": "Tashkent",
            "photo": "photo_data", "bio": "Hello Kairyx", "interests": ["🎮 Gaming", "🎵 Music"],
            "terms_accepted": True
        }
        resp = await self.client.post("/api/register?initData=mock_user", json=valid_payload)
        self.assertEqual(resp.status, 200)
        data = await resp.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["user_status"], "PENDING_APPROVAL")

    async def test_profile_edit_and_delete(self):
        await self.clear_db()
        await self.client.get("/api/session?initData=mock_user")
        await self.client.post("/api/register?initData=mock_user", json={
            "name": "Original Name", "age": 25, "city": "Tashkent",
            "photo": "photo_data", "bio": "Bio", "terms_accepted": True
        })

        # Edit Profile
        resp_edit = await self.client.post("/api/profile/update?initData=mock_user", json={
            "name": "Updated Name", "city": "Samarkand", "bio": "New Bio", "interests": ["✈️ Travel"]
        })
        self.assertEqual(resp_edit.status, 200)
        data_edit = await resp_edit.json()
        self.assertEqual(data_edit["user"]["name"], "Updated Name")
        self.assertEqual(data_edit["user"]["city"], "Samarkand")

        # Deactivate / Delete Account
        resp_del = await self.client.post("/api/account/delete?initData=mock_user")
        self.assertEqual(resp_del.status, 200)

    async def test_admin_security_and_management(self):
        await self.clear_db()

        # Non-admin forbidden
        resp_forbid = await self.client.get("/api/admin/stats?initData=mock_user")
        self.assertEqual(resp_forbid.status, 403)

        resp_forbid_rep = await self.client.get("/api/admin/reports?initData=mock_user")
        self.assertEqual(resp_forbid_rep.status, 403)

        # Admin authorized
        resp_adm = await self.client.get("/api/admin/stats?initData=mock_admin")
        self.assertEqual(resp_adm.status, 200)
        data_adm = await resp_adm.json()
        self.assertTrue(data_adm["success"])

    async def test_full_dating_safety_and_filtering(self):
        await self.clear_db()

        # 1. Create two users
        await self.client.get("/api/session?initData=mock_user_1")
        await self.client.post("/api/register?initData=mock_user_1", json={
            "name": "User One", "age": 22, "city": "Tashkent",
            "photo": "photo1", "bio": "Bio 1", "interests": ["🎮 Gaming"],
            "terms_accepted": True
        })

        await self.client.get("/api/session?initData=mock_user_2")
        await self.client.post("/api/register?initData=mock_user_2", json={
            "name": "User Two", "age": 28, "city": "Samarkand",
            "photo": "photo2", "bio": "Bio 2", "interests": ["✈️ Travel"],
            "terms_accepted": True
        })

        # Admin approves both
        resp_p = await self.client.get("/api/admin/pending?initData=mock_admin")
        data_p = await resp_p.json()
        u1_id = next(u["id"] for u in data_p["users"] if u["name"] == "User One")
        u2_id = next(u["id"] for u in data_p["users"] if u["name"] == "User Two")

        await self.client.post("/api/admin/approve?initData=mock_admin", json={"user_id": u1_id})
        await self.client.post("/api/admin/approve?initData=mock_admin", json={"user_id": u2_id})

        # Filter test: age range 25-30 matches User 2
        resp_f1 = await self.client.get("/api/profiles?min_age=25&max_age=30&initData=mock_user_1")
        self.assertEqual(len((await resp_f1.json())["profiles"]), 1)

        # Filter test: age range 18-24 excludes User 2
        resp_f2 = await self.client.get("/api/profiles?min_age=18&max_age=24&initData=mock_user_1")
        self.assertEqual(len((await resp_f2.json())["profiles"]), 0)

        # Swipes & Match
        await self.client.post("/api/swipe?initData=mock_user_1", json={"target_id": u2_id, "is_like": True})
        resp_m = await self.client.post("/api/swipe?initData=mock_user_2", json={"target_id": u1_id, "is_like": True})
        data_m = await resp_m.json()
        self.assertTrue(data_m["match"])
        match_id = data_m["match_id"]

        # Messaging
        await self.client.post("/api/chat/send?initData=mock_user_1", json={"match_id": match_id, "text": "Salom!"})
        resp_msgs = await self.client.get(f"/api/chat/messages?match_id={match_id}&initData=mock_user_2")
        self.assertEqual(len((await resp_msgs.json())["messages"]), 2)

        # Report & Admin moderation
        await self.client.post("/api/user/report?initData=mock_user_1", json={
            "target_id": u2_id, "reason": "Harassment", "description": "Test report"
        })
        resp_reps = await self.client.get("/api/admin/reports?initData=mock_admin")
        self.assertEqual(len((await resp_reps.json())["reports"]), 1)
        r_id = (await resp_reps.json())["reports"][0]["id"]
        await self.client.post("/api/admin/report/resolve?initData=mock_admin", json={"report_id": r_id, "action": "RESOLVE"})

        # Block & Unblock
        await self.client.post("/api/user/block?initData=mock_user_1", json={"target_id": u2_id})
        resp_b_list = await self.client.get("/api/user/blocked?initData=mock_user_1")
        self.assertEqual(len((await resp_b_list.json())["blocked_users"]), 1)

        await self.client.post("/api/user/unblock?initData=mock_user_1", json={"target_id": u2_id})
        resp_unb_list = await self.client.get("/api/user/blocked?initData=mock_user_1")
        self.assertEqual(len((await resp_unb_list.json())["blocked_users"]), 0)
