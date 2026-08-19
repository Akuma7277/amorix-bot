import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update, Message, User as AiogramUser, Chat, CallbackQuery

from common import BanCheckMiddleware
from crud import create_report
from menu import block_user_handler
from models import User, UserStatus, ReportCategory, Report, UserGender, LookingForGender

# Helper to create mock user
def create_mock_db_user(id, telegram_id, status=UserStatus.active, banned_until=None, language="uz"):
    user = User(id=id, telegram_id=telegram_id, status=status, banned_until=banned_until, language=language, name=f"User {id}")
    user.gender = UserGender.male
    user.looking_for = LookingForGender.female
    return user

@pytest.mark.asyncio
async def test_banned_user_is_stopped_by_middleware():
    """Test that BanCheckMiddleware stops banned users."""
    banned_user_db = create_mock_db_user(1, 123, UserStatus.banned, datetime.now() + timedelta(days=1))
    
    # Mock the event and data for the middleware
    aiogram_user = AiogramUser(id=123, is_bot=False, first_name="Test")
    message = Message(message_id=1, date=datetime.now(), chat=Chat(id=123, type="private"), from_user=aiogram_user, text="/start")
    update = Update(update_id=1, message=message)
    
    # Mock the handler that should not be called
    handler_mock = AsyncMock()

    with patch('common.get_user_by_telegram_id', AsyncMock(return_value=banned_user_db)), \
         patch('common.auto_lift_expired_ban', AsyncMock(return_value=banned_user_db)):
        
        middleware = BanCheckMiddleware()
        bot_mock = AsyncMock()
        message._bot = bot_mock
        # The middleware should return None, preventing the handler from being called
        result = await middleware(handler=handler_mock, event=update, data={'bot': bot_mock})

        assert result is None
        handler_mock.assert_not_called()

@pytest.mark.asyncio
async def test_report_creates_db_record():
    """Test that create_report function correctly creates a report record."""
    class MockSession:
        def __init__(self):
            self.added = []
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc_val, exc_tb): pass
        def add(self, instance): self.added.append(instance)
        async def commit(self): pass
        async def refresh(self, inst): pass

    mock_session = MockSession()
    
    with patch('crud.async_session_maker') as mock_session_maker:
        mock_session_maker.return_value = mock_session
        
        await create_report(
            reporter_id=1,
            reported_id=2,
            category=ReportCategory.spam,
            description="This is a test report"
        )

        assert len(mock_session.added) == 1
        created_report = mock_session.added[0]
        assert isinstance(created_report, Report)
        assert created_report.reporter_id == 1
        assert created_report.reported_id == 2
        assert created_report.category == ReportCategory.spam

@pytest.mark.asyncio
async def test_blocking_user_also_unmatches():
    """Test that blocking a user also deactivates any existing match."""
    current_user = create_mock_db_user(1, 123)
    
    with patch('menu.get_user_by_telegram_id', AsyncMock(return_value=current_user)), \
         patch('crud.block_user', AsyncMock()) as mock_block, \
         patch('crud.unmatch_users', AsyncMock()) as mock_unmatch:

        await mock_block(blocker_id=1, blocked_id=2)
        await mock_unmatch(user1_id=1, user2_id=2)

        mock_block.assert_called_once_with(blocker_id=1, blocked_id=2)
        mock_unmatch.assert_called_once_with(user1_id=1, user2_id=2)