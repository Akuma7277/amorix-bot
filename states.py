from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    choosing_language = State()
    accepting_terms = State()
    entering_name = State()
    entering_age = State()
    choosing_gender = State()
    entering_height = State()
    choosing_looking_for = State()
    choosing_intent = State()
    entering_city = State()
    choosing_city = State()
    entering_district = State()
    choosing_interests = State()
    entering_bio = State()
    confirming_ai_bio = State()
    uploading_photos = State()
    reviewing_profile = State()
    # Keyingi bosqichlar shu yerga qo'shiladi


class MenuStates(StatesGroup):
    searching = State()
    in_chat = State()
    viewing_help = State() # Added for help section
    viewing_referrals = State() # Added for referral system
    confirm_block = State() # Added for user blocking
    viewing_likes = State()
    writing_to_admin = State() # Foydalanuvchi adminga xabar yozayotgan holat
    # NEW GIFT STATES
    choosing_gift_type = State()
    entering_gift_message = State()
    confirming_gift = State()
    # Advanced Search states
    setting_min_age = State()
    setting_max_age = State()
    setting_region = State()
    setting_min_height = State()
    setting_max_height = State()
    performing_advanced_search = State()

class EditingStates(StatesGroup):
    choosing_field = State()
    editing_name = State()
    editing_bio = State()
    confirming_ai_bio = State()
    editing_city = State()
    editing_district = State()
    editing_interests = State()
    editing_photos = State()
    editing_height = State()


class AdminStates(StatesGroup):
    main_menu = State()
    statistics = State()
    verification_moderation = State()
    photo_moderation = State()
    user_management = State()
    waiting_for_user_id = State()
    viewing_user = State()
    report_moderation = State()
    waiting_for_broadcast_message = State()
    choosing_broadcast_target = State()
    confirming_broadcast = State()
    tariffs_payments = State()
    payment_moderation = State()
    viewing_logs = State()
    choosing_log_filter = State()
    choosing_log_action = State()
    entering_log_date = State()
    viewing_admins = State()
    waiting_for_admin_id_to_add = State()
    setting_channel = State()
    waiting_for_channel_id = State()
    managing_districts = State()
    waiting_for_district_to_add = State()
    waiting_for_district_to_remove = State()


class SettingsStates(StatesGroup):
    main_menu = State()
    confirm_hide_profile = State()
    confirm_delete_account = State()
    choosing_language = State()

class VerificationStates(StatesGroup):
    uploading_document = State()
    confirming_submission = State()

class PremiumStates(StatesGroup):
    main_menu = State()
    choosing_plan = State()
    confirming_payment = State()



class ReportingStates(StatesGroup):
    choosing_category = State()
    entering_description = State()