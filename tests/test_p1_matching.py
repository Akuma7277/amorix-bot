import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta
import unittest

import crud
from models import User, UserStatus, Like, Match, ChatMessage, Notification, PremiumPlan
from sqlalchemy import select, and_, or_
from webapp.api import require_approved_user
from aiohttp import web

class FakeRequest:
    def __init__(self, headers=None, query=None):
        self.headers = headers or {}
        self.query = query or {}

class P1MatchingTests(unittest.IsolatedAsyncioTestCase):
    
    @patch('webapp.api.get_telegram_user')
    async def test_require_approved_user_blocks_non_active(self, mock_get_tg):
        mock_get_tg.return_value = {'id': 12345}
        pending_user = User(id=1, telegram_id=12345, status=UserStatus.pending_approval, name='Tester')
        
        class FakeSession:
            async def __aenter__(self):
                return self
            async def __aexit__(self, exc_type, exc, tb):
                pass
            async def execute(self, stmt):
                class MockResult:
                    def scalar_one_or_none(self):
                        return pending_user
                return MockResult()
                
        with patch('webapp.api.async_session_maker', lambda: FakeSession()):
            request = FakeRequest(headers={'X-Telegram-Init-Data': 'some_data'})
            with self.assertRaises(web.HTTPForbidden):
                await require_approved_user(request)
                
    @patch('webapp.api.get_telegram_user')
    async def test_require_approved_user_allows_active(self, mock_get_tg):
        mock_get_tg.return_value = {'id': 12345}
        active_user = User(id=1, telegram_id=12345, status=UserStatus.active, name='Tester')
        
        class FakeSession:
            async def __aenter__(self):
                return self
            async def __aexit__(self, exc_type, exc, tb):
                pass
            async def execute(self, stmt):
                class MockResult:
                    def scalar_one_or_none(self):
                        return active_user
                return MockResult()
                
        with patch('webapp.api.async_session_maker', lambda: FakeSession()):
            request = FakeRequest(headers={'X-Telegram-Init-Data': 'some_data'})
            tg_user, db_user = await require_approved_user(request)
            self.assertEqual(db_user.status, UserStatus.active)
            self.assertEqual(db_user.name, 'Tester')
