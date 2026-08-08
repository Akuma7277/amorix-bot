import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from menu import who_liked_me_handler, activate_boost_handler, PREMIUM_REQUIRED_TEXTS, WHO_LIKED_ME_EMPTY_TEXTS, LIKES_VIEW_TEXTS, BOOST_ACTIVATED_TEXTS
from models import User, PremiumPlan, UserStatus, VerificationStatus
from states import MenuStates

# Helper to create mock user
def create_mock_user_for_premium(id, telegram_id, premium_plan=PremiumPlan.basic, expires_at=None, language="uz"):
    user = User(id=id, telegram_id=telegram_id, premium_plan=premium_plan, premium_expires_at=expires_at, language=language)
    # Add other necessary fields for has_active_premium check
    user.name = "Test"
    user.status = UserStatus.active
    user.verification_status = VerificationStatus.not_verified # Default for tests
    return user

# Helper to create mock callback and state
async def get_mock_callback_and_state(user_telegram_id):
    callback = AsyncMock()
    callback.from_user.id = user_telegram_id
    # Mock message attribute on callback
    callback.message = AsyncMock()
    storage = MemoryStorage()
    state = FSMContext(storage, chat_id=user_telegram_id, user_id=user_telegram_id)
    return callback, state


@pytest.mark.asyncio
async def test_basic_user_cannot_see_who_liked_me():
    """A basic user should get a 'premium required' message."""
    user = create_mock_user_for_premium(1, 123, PremiumPlan.basic)
    callback, state = await get_mock_callback_and_state(123)

    with patch('menu.get_user_by_telegram_id', AsyncMock(return_value=user)):
        await who_liked_me_handler(callback, state)

    callback.answer.assert_called_once_with(
        PREMIUM_REQUIRED_TEXTS["uz"], show_alert=True
    )

@pytest.mark.asyncio
async def test_premium_user_with_no_likes_gets_empty_message():
    """A premium user with no likes should get an 'empty' message."""
    user = create_mock_user_for_premium(1, 123, PremiumPlan.gold, datetime.now() + timedelta(days=1))
    callback, state = await get_mock_callback_and_state(123)

    with patch('menu.get_user_by_telegram_id', AsyncMock(return_value=user)), \
         patch('menu.get_users_who_liked_me_full', AsyncMock(return_value=[])):
        
        await who_liked_me_handler(callback, state)

        callback.message.answer.assert_called_once_with(WHO_LIKED_ME_EMPTY_TEXTS["uz"])
        current_state = await state.get_state()
        assert current_state is None # State should not be set

@pytest.mark.asyncio
async def test_premium_user_with_likes_enters_viewing_flow():
    """A premium user with likes should enter the viewing flow."""
    user = create_mock_user_for_premium(1, 123, PremiumPlan.gold, datetime.now() + timedelta(days=1))
    liker = create_mock_user_for_premium(2, 456)
    callback, state = await get_mock_callback_and_state(123)

    with patch('menu.get_user_by_telegram_id', AsyncMock(return_value=user)), \
         patch('menu.get_users_who_liked_me_full', AsyncMock(return_value=[liker])), \
         patch('menu.show_next_liked_profile', AsyncMock()) as mock_show_next:

        await who_liked_me_handler(callback, state)

        current_state = await state.get_state()
        assert current_state == MenuStates.viewing_likes
        
        data = await state.get_data()
        assert data['liked_profiles'] == [2]

        callback.message.answer.assert_called_once_with(LIKES_VIEW_TEXTS["uz"])
        mock_show_next.assert_called_once()


@pytest.mark.asyncio
async def test_basic_user_cannot_activate_boost():
    """A basic user should not be able to activate boost."""
    user = create_mock_user_for_premium(1, 123, PremiumPlan.basic)
    callback, _ = await get_mock_callback_and_state(123)

    with patch('menu.get_user_by_telegram_id', AsyncMock(return_value=user)), \
         patch('crud.activate_profile_boost', AsyncMock(return_value=None)): # Mock crud function to return None for non-premium
        await activate_boost_handler(callback)

    callback.answer.assert_called_once_with(
        PREMIUM_REQUIRED_TEXTS["uz"], show_alert=True
    )

@pytest.mark.asyncio
async def test_premium_user_can_activate_boost():
    """A premium user should be able to activate boost."""
    user = create_mock_user_for_premium(1, 123, PremiumPlan.gold, datetime.now() + timedelta(days=1))
    callback, _ = await get_mock_callback_and_state(123)
    
    # Mock the crud function to return a future datetime
    mock_expires_at = datetime.now() + timedelta(minutes=30) # Using a fixed value for test
    with patch('menu.get_user_by_telegram_id', AsyncMock(return_value=user)), \
         patch('crud.activate_profile_boost', AsyncMock(return_value=mock_expires_at)), \
         patch('crud.is_boost_active', AsyncMock(return_value=False)): # Ensure boost is not already active
        await activate_boost_handler(callback)

    callback.answer.assert_called_once_with() # No alert means success
    callback.message.answer.assert_called_once_with(
        BOOST_ACTIVATED_TEXTS["uz"].format(minutes=30) # Using 30 as per BOOST_DURATION_MINUTES
    )

@pytest.mark.asyncio
async def test_active_boost_is_not_re_added():
    """If boost is already active, it should not be re-added, but show remaining time."""
    user = create_mock_user_for_premium(1, 123, PremiumPlan.gold, datetime.now() + timedelta(days=1))
    callback, _ = await get_mock_callback_and_state(123)

    # Mock boost as already active
    with patch('menu.get_user_by_telegram_id', AsyncMock(return_value=user)), \
         patch('crud.is_boost_active', AsyncMock(return_value=True)), \
         patch('crud.get_boost_remaining_minutes', AsyncMock(return_value=15)): # Assume 15 minutes remaining
        await activate_boost_handler(callback)

    callback.answer.assert_called_once_with(
        "🚀 Profilingiz allaqachon Boost qilingan. Qolgan vaqt: 15 daqiqa.",
        show_alert=True
    )
    callback.message.answer.assert_not_called() # No new message should be sent

@pytest.mark.asyncio
async def test_expired_boost_is_not_active():
    """An expired boost should not be considered active."""
    user = create_mock_user_for_premium(1, 123, PremiumPlan.gold, datetime.now() + timedelta(days=1))
    user.boost_active_until = datetime.now() - timedelta(minutes=1) # Boost expired
    
    # Test is_boost_active directly
    with patch('crud.async_session_maker', AsyncMock()) as mock_session_maker:
        mock_session_maker.return_value.__aenter__.return_value.get.return_value = user
        is_active = await crud.is_boost_active(user.id)
        assert not is_active
