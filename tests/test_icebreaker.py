import pytest
import random
from unittest.mock import AsyncMock, patch

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from menu import icebreaker_handler, MATCH_NOT_FOUND_OR_INACTIVE_TEXTS, ICEBREAKER_SENT_TEXTS
from models import User, Match, UserStatus, PremiumPlan, UserGender, LookingForGender
from common import ICEBREAKER_QUESTIONS

# Helper to create mock user
def create_mock_user_for_icebreaker(id, telegram_id, language="uz"):
    user = User(id=id, telegram_id=telegram_id, language=language, name=f"User {id}", status=UserStatus.active)
    user.premium_plan = PremiumPlan.basic
    user.gender = UserGender.male
    user.looking_for = LookingForGender.female
    return user

# Helper to create mock callback and state
async def get_mock_callback_and_state(user_telegram_id, data_str):
    callback = AsyncMock()
    callback.from_user.id = user_telegram_id
    callback.data = data_str
    callback.message = AsyncMock()
    storage = MemoryStorage()
    state = FSMContext(storage, chat_id=user_telegram_id, user_id=user_telegram_id)
    return callback, state

@pytest.mark.asyncio
async def test_icebreaker_sends_message_successfully():
    """Test that the icebreaker handler correctly sends a message on a valid match."""
    sender = create_mock_user_for_icebreaker(1, 123, "uz")
    recipient = create_mock_user_for_icebreaker(2, 456, "ru")
    match = Match(id=10, user1_id=sender.id, user2_id=recipient.id, is_active=True)
    
    callback, state = await get_mock_callback_and_state(sender.telegram_id, "icebreaker_10")
    bot_mock = AsyncMock()
    
    random.seed(0) # for predictable random.choice
    expected_question_ru = ICEBREAKER_QUESTIONS["ru"][0]

    with patch('menu.get_user_by_telegram_id', AsyncMock(return_value=sender)), \
         patch('menu.get_match_by_id', AsyncMock(return_value=match)), \
         patch('menu.get_user_by_id', AsyncMock(side_effect=lambda id: recipient if id == recipient.id else None)), \
         patch('menu.create_chat_message', AsyncMock()) as mock_create_chat, \
         patch('random.choice', return_value=expected_question_ru) as mock_random_choice:

        await icebreaker_handler(callback, state, bot_mock)

        # 1. Check if it tried to get the question in the recipient's language
        mock_random_choice.assert_called_once_with(ICEBREAKER_QUESTIONS["ru"])

        # 2. Check if message was saved to DB
        mock_create_chat.assert_called_once_with(
            match_id=match.id,
            sender_id=sender.id,
            text=expected_question_ru
        )

        # 3. Check if message was sent to recipient
        bot_mock.send_message.assert_called_once()
        call_args = bot_mock.send_message.call_args[1]
        assert call_args['chat_id'] == recipient.telegram_id
        assert expected_question_ru in call_args['text']

        # 4. Check if sender got confirmation
        callback.answer.assert_called_once_with(ICEBREAKER_SENT_TEXTS["uz"], show_alert=True)
        callback.message.answer.assert_called_once()
        confirm_text_args = callback.message.answer.call_args[0]
        assert expected_question_ru in confirm_text_args[0]

@pytest.mark.asyncio
async def test_icebreaker_fails_for_invalid_match():
    """Test that the handler shows an error for a non-existent match."""
    sender = create_mock_user_for_icebreaker(1, 123, "uz")
    callback, state = await get_mock_callback_and_state(sender.telegram_id, "icebreaker_999")
    bot_mock = AsyncMock()

    with patch('menu.get_user_by_telegram_id', AsyncMock(return_value=sender)), \
         patch('menu.get_match_by_id', AsyncMock(return_value=None)):

        await icebreaker_handler(callback, state, bot_mock)

        callback.answer.assert_called_once_with(MATCH_NOT_FOUND_OR_INACTIVE_TEXTS["uz"], show_alert=True)
        bot_mock.send_message.assert_not_called()

@pytest.mark.asyncio
async def test_icebreaker_fails_for_user_not_in_match():
    """Test that a user who is not part of the match cannot trigger the icebreaker."""
    user1 = create_mock_user_for_icebreaker(1, 123)
    user2 = create_mock_user_for_icebreaker(2, 456)
    imposter = create_mock_user_for_icebreaker(3, 789) # The one making the call
    match = Match(id=11, user1_id=user1.id, user2_id=user2.id, is_active=True)

    callback, state = await get_mock_callback_and_state(imposter.telegram_id, "icebreaker_11")
    bot_mock = AsyncMock()

    with patch('menu.get_user_by_telegram_id', AsyncMock(return_value=imposter)), \
         patch('menu.get_match_by_id', AsyncMock(return_value=match)):

        await icebreaker_handler(callback, state, bot_mock)

        callback.answer.assert_called_once_with(MATCH_NOT_FOUND_OR_INACTIVE_TEXTS["uz"], show_alert=True)
        bot_mock.send_message.assert_not_called()