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
        self.assertFalse(data["is_admin"])

    async def test_session_authorized_admin(self):
        await self.clear_db()
        resp = await self.client.get("/api/session?initData=mock_admin")
        self.assertEqual(resp.status, 200)
        data = await resp.json()
        self.assertTrue(data["success"])
        self.assertTrue(data["is_admin"])

    async def test_admin_pending_endpoints_forbidden(self):
        await self.clear_db()
        resp = await self.client.get("/api/admin/pending?initData=mock_user")
        self.assertEqual(resp.status, 403)

    async def test_admin_flow_approve_and_reject(self):
        await self.clear_db()
        
        # 1. Create a user and submit registration
        await self.client.get("/api/session?initData=mock_user")
        payload = {
            "name": "Jane Doe",
            "age": 22,
            "city": "Tashkent",
            "photo": "data:image/png;base64,mock...",
            "bio": "Hello Kairyx",
            "terms_accepted": True
        }
        await self.client.post("/api/register?initData=mock_user", json=payload)

        # 2. Get pending list as admin
        resp_pending = await self.client.get("/api/admin/pending?initData=mock_admin")
        self.assertEqual(resp_pending.status, 200)
        data_pending = await resp_pending.json()
        self.assertTrue(data_pending["success"])
        self.assertEqual(len(data_pending["users"]), 1)
        db_user_id = data_pending["users"][0]["id"]

        # 3. Approve user
        resp_approve = await self.client.post("/api/admin/approve?initData=mock_admin", json={"user_id": db_user_id})
        self.assertEqual(resp_approve.status, 200)
        data_approve = await resp_approve.json()
        self.assertTrue(data_approve["success"])

        # 4. Verify user status is now APPROVED
        resp_session = await self.client.get("/api/session?initData=mock_user")
        data_session = await resp_session.json()
        self.assertEqual(data_session["user_status"], "APPROVED")
