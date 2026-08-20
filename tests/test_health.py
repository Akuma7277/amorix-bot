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

    async def test_register_validation_underage(self):
        await self.clear_db()
        await self.client.get("/api/session?initData=mock_user")
        payload = {
            "name": "Jane Doe",
            "age": 17,
            "city": "Tashkent",
            "photo": "data:image/png;base64,mock...",
            "bio": "Dating bio",
            "terms_accepted": True
        }
        resp = await self.client.post("/api/register?initData=mock_user", json=payload)
        self.assertEqual(resp.status, 400)
        data = await resp.json()
        self.assertEqual(data["error"]["code"], "UNDERAGE")

    async def test_register_validation_missing_fields(self):
        await self.clear_db()
        await self.client.get("/api/session?initData=mock_user")
        payload = {
            "name": "",
            "age": 20,
            "city": "Tashkent",
            "photo": "",
            "bio": "Dating bio",
            "terms_accepted": True
        }
        resp = await self.client.post("/api/register?initData=mock_user", json=payload)
        self.assertEqual(resp.status, 400)
        data = await resp.json()
        self.assertEqual(data["error"]["code"], "MISSING_FIELDS")

    async def test_register_success_transitions_to_pending(self):
        await self.clear_db()
        await self.client.get("/api/session?initData=mock_user")
        payload = {
            "name": "Jane Doe",
            "age": 22,
            "city": "Tashkent",
            "photo": "data:image/png;base64,mock...",
            "bio": "Hello Kairyx",
            "terms_accepted": True
        }
        resp = await self.client.post("/api/register?initData=mock_user", json=payload)
        self.assertEqual(resp.status, 200)
        data = await resp.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["user_status"], "PENDING_APPROVAL")

        # Session should now return PENDING_APPROVAL
        resp_session = await self.client.get("/api/session?initData=mock_user")
        self.assertEqual(resp_session.status, 200)
        data_session = await resp_session.json()
        self.assertEqual(data_session["user_status"], "PENDING_APPROVAL")
