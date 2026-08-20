import unittest
from aiohttp import web
from webapp.api import create_webapp_app
from aiohttp.test_utils import AioHTTPTestCase

class TestHealthEndpoints(AioHTTPTestCase):
    async def get_application(self):
        return create_webapp_app()

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

    async def test_session_authorized(self):
        resp = await self.client.get("/api/session?initData=mock_user")
        self.assertEqual(resp.status, 200)
        data = await resp.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["user_status"], "DRAFT")
