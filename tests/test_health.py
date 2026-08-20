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
        self.assertEqual(data["service"], "kairyx-api")
        self.assertIn("timestamp", data)

    async def test_health_ready_endpoint(self):
        resp = await self.client.get("/health/ready")
        self.assertIn(resp.status, [200, 503])
        data = await resp.json()
        self.assertIn(data["status"], ["ready", "unhealthy"])
