from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    gender = State()
    phone = State()
    region = State()
    district = State()
    age = State()
    height = State()
    weight = State()
    photos = State()
    bio = State()


class AdminStates(StatesGroup):
    waiting_broadcast = State()
    waiting_channel = State()
    waiting_user_search = State()
