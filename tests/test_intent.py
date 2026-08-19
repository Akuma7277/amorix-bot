import pytest
from unittest.mock import AsyncMock, patch

from models import User, RelationshipIntent, UserGender, LookingForGender
from crud import calculate_compatibility_score, get_compatibility_reasons
from registration import intent_chosen
from states import RegistrationStates
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage

def create_mock_user_for_intent(id, intent=None):
    """Helper to create a mock user with a specific intent."""
    if id == 1:
        return User(
            id=id,
            telegram_id=id,
            name=f"User {id}",
            age=20,
            gender=UserGender.male,
            looking_for=LookingForGender.female,
            interests="a",
            city="Tashkent",
            relationship_intent=intent
        )
    else:
        return User(
            id=id,
            telegram_id=id,
            name=f"User {id}",
            age=50,
            gender=UserGender.female,
            looking_for=LookingForGender.male,
            interests="b",
            city="Tashkent",
            relationship_intent=intent
        )

@pytest.mark.asyncio
async def test_compatibility_score_intent_match():
    """Test compatibility score for matching intents."""
    user1 = create_mock_user_for_intent(1, RelationshipIntent.serious)
    user2 = create_mock_user_for_intent(2, RelationshipIntent.serious)

    with patch('crud.async_session_maker') as mock_session_maker:
        mock_session_maker.return_value.__aenter__.return_value.get.side_effect = [user1, user2]
        with patch('crud.get_user_photos', AsyncMock(return_value=[])):
            # Score without intent: 10(gender) + 10(city) = 20
            # With exact intent match: 20 + 15 = 35
            score = await calculate_compatibility_score(user1.id, user2.id)
            assert score == 35

@pytest.mark.asyncio
async def test_compatibility_score_intent_compatible():
    """Test compatibility score for compatible (but not exact) intents."""
    user1 = create_mock_user_for_intent(1, RelationshipIntent.serious)
    user2 = create_mock_user_for_intent(2, RelationshipIntent.marriage)

    with patch('crud.async_session_maker') as mock_session_maker:
        mock_session_maker.return_value.__aenter__.return_value.get.side_effect = [user1, user2]
        with patch('crud.get_user_photos', AsyncMock(return_value=[])):
            # Score without intent: 20
            # With compatible intent: 20 + 10 = 30
            score = await calculate_compatibility_score(user1.id, user2.id)
            assert score == 30

@pytest.mark.asyncio
async def test_compatibility_score_intent_private():
    """Test compatibility score when one user's intent is private."""
    user1 = create_mock_user_for_intent(1, RelationshipIntent.serious)
    user2 = create_mock_user_for_intent(2, RelationshipIntent.private)

    with patch('crud.async_session_maker') as mock_session_maker:
        mock_session_maker.return_value.__aenter__.return_value.get.side_effect = [user1, user2]
        with patch('crud.get_user_photos', AsyncMock(return_value=[])):
            # Score without intent: 20
            # With private intent: 20 + 5 = 25
            score = await calculate_compatibility_score(user1.id, user2.id)
            assert score == 25

@pytest.mark.asyncio
async def test_compatibility_score_intent_conflict():
    """Test compatibility score for conflicting intents."""
    user1 = create_mock_user_for_intent(1, RelationshipIntent.serious)
    user2 = create_mock_user_for_intent(2, RelationshipIntent.friendship)

    with patch('crud.async_session_maker') as mock_session_maker:
        mock_session_maker.return_value.__aenter__.return_value.get.side_effect = [user1, user2]
        with patch('crud.get_user_photos', AsyncMock(return_value=[])):
            # Score without intent: 20
            # With conflicting intent: 20 + 0 = 20
            score = await calculate_compatibility_score(user1.id, user2.id)
            assert score == 20

@pytest.mark.asyncio
async def test_registration_intent_step():
    """Test that the intent selection step works in registration."""
    callback = AsyncMock()
    callback.data = "intent_serious"
    callback.message = AsyncMock()
    storage = MemoryStorage()
    state = FSMContext(storage, key=StorageKey(bot_id=123, chat_id=123, user_id=123))
    await state.update_data(language="uz")

    await intent_chosen(callback, state)

    data = await state.get_data()
    current_state = await state.get_state()

    assert data['relationship_intent'] == 'serious'
    assert current_state == RegistrationStates.entering_city
    callback.message.edit_text.assert_called_once()