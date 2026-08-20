import unittest
from aiohttp import web
from webapp.api import create_webapp_app
from aiohttp.test_utils import AioHTTPTestCase

class TestHealthEndpoints(AioHTTPTestCase):
    async def get_application(self):
        return create_webapp_app()

    async def clear_db(self):
        from engine import async_session_maker
        from sqlalchemy import text
        try:
            async with async_session_maker() as session:
                await session.execute(text("DELETE FROM messages;"))
                await session.execute(text("DELETE FROM matches;"))
                await session.execute(text("DELETE FROM swipes;"))
                await session.execute(text("DELETE FROM users;"))
                await session.commit()
        except Exception as e:
            print("clear_db warning:", e)

    async def test_health_endpoint(self):
        resp = await self.client.get("/health")
        self.assertEqual(resp.status, 200)
        data = await resp.json()
        self.assertEqual(data["status"], "ok")

    async def test_health_ready_endpoint(self):
        resp = await self.client.get("/health/ready")
        self.assertEqual(resp.status, 200)
        data = await resp.json()
        self.assertEqual(data["status"], "ready")

    async def test_session_unauthorized(self):
        resp = await self.client.get("/api/session")
        self.assertEqual(resp.status, 401)
        data = await resp.json()
        self.assertFalse(data["success"])

    async def test_session_authorized_creates_draft(self):
        await self.clear_db()
        resp = await self.client.get("/api/session?initData=mock_user")
        self.assertEqual(resp.status, 200)
        data = await resp.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["user_status"], "DRAFT")

    async def test_dating_lifecycle(self):
        await self.clear_db()
        
        # 1. Create two users and approve them
        # User 1
        await self.client.get("/api/session?initData=mock_user_1")
        payload1 = {
            "name": "User One", "age": 22, "city": "Tashkent",
            "photo": "photo1", "bio": "Bio 1", "terms_accepted": True
        }
        await self.client.post("/api/register?initData=mock_user_1", json=payload1)
        
        # User 2
        await self.client.get("/api/session?initData=mock_user_2")
        payload2 = {
            "name": "User Two", "age": 24, "city": "Samarkand",
            "photo": "photo2", "bio": "Bio 2", "terms_accepted": True
        }
        await self.client.post("/api/register?initData=mock_user_2", json=payload2)

        # Get DB IDs of both users as Admin
        resp_pending = await self.client.get("/api/admin/pending?initData=mock_admin")
        pending_data = await resp_pending.json()
        self.assertEqual(len(pending_data["users"]), 2)
        
        id1 = next(u["id"] for u in pending_data["users"] if u["name"] == "User One")
        id2 = next(u["id"] for u in pending_data["users"] if u["name"] == "User Two")

        # Approve both users
        await self.client.post("/api/admin/approve?initData=mock_admin", json={"user_id": id1})
        await self.client.post("/api/admin/approve?initData=mock_admin", json={"user_id": id2})

        # 2. User 1 checks profiles for swiping (should contain User 2)
        resp_prof = await self.client.get("/api/profiles?initData=mock_user_1")
        prof_data = await resp_prof.json()
        self.assertTrue(prof_data["success"])
        self.assertEqual(len(prof_data["profiles"]), 1)
        self.assertEqual(prof_data["profiles"][0]["name"], "User Two")

        # 3. User 1 swipes Like on User 2 (no match yet)
        resp_swipe1 = await self.client.post("/api/swipe?initData=mock_user_1", json={"target_id": id2, "is_like": True})
        swipe1_data = await resp_swipe1.json()
        self.assertTrue(swipe1_data["success"])
        self.assertFalse(swipe1_data["match"])

        # 4. User 2 swipes Like on User 1 (Match created!)
        resp_swipe2 = await self.client.post("/api/swipe?initData=mock_user_2", json={"target_id": id1, "is_like": True})
        swipe2_data = await resp_swipe2.json()
        self.assertTrue(swipe2_data["success"])
        self.assertTrue(swipe2_data["match"])
        match_id = swipe2_data["match_id"]

        # 5. User 1 sends a chat message
        resp_send = await self.client.post("/api/chat/send?initData=mock_user_1", json={"match_id": match_id, "text": "Hello User Two!"})
        send_data = await resp_send.json()
        self.assertTrue(send_data["success"])

        # 6. User 2 reads chat messages (should contain system greeting and User 1 message)
        resp_msgs = await self.client.get(f"/api/chat/messages?match_id={match_id}&initData=mock_user_2")
        msgs_data = await resp_msgs.json()
        self.assertTrue(msgs_data["success"])
        self.assertEqual(len(msgs_data["messages"]), 2)
        self.assertEqual(msgs_data["messages"][0]["sender_id"], 0) # System greeting
        self.assertEqual(msgs_data["messages"][1]["text"], "Hello User Two!")
