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

    async def test_api_test_endpoint(self):
        resp = await self.client.get("/api/test")
        self.assertEqual(resp.status, 200)
        data = await resp.json()
        self.assertEqual(data["message"], "api works")
