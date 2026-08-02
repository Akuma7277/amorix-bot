import unittest

from inline import (
    get_admin_dashboard_keyboard,
    get_district_keyboard,
    get_search_keyboard,
    get_city_keyboard,
    resolve_region_name,
    get_help_keyboard,
    get_profile_approval_keyboard,
    get_manage_admins_keyboard,
)


class InlineKeyboardTests(unittest.TestCase):
    def test_search_keyboard_includes_super_like_and_block_actions(self):
        keyboard = get_search_keyboard("uz", target_user_id=7)
        callbacks = [
            button.callback_data
            for row in keyboard.inline_keyboard
            for button in row
            if button.callback_data
        ]

        self.assertIn("super_like_7", callbacks)
        self.assertIn("block_7", callbacks)

    def test_admin_dashboard_keyboard_contains_quick_actions(self):
        keyboard = get_admin_dashboard_keyboard("uz")
        callbacks = [
            button.callback_data
            for row in keyboard.inline_keyboard
            for button in row
            if button.callback_data
        ]

        self.assertIn("admin_stats", callbacks)
        self.assertIn("admin_payments", callbacks)

    def test_region_name_resolution_keeps_tashkent_city_region(self):
        self.assertEqual(resolve_region_name("toshkent_shahri"), "Toshkent shahri")

    def test_tashkent_city_region_shows_districts(self):
        keyboard = get_district_keyboard("Toshkent shahri", "uz")
        labels = [button.text for row in keyboard.inline_keyboard for button in row]

        self.assertIn("Yunusobod", labels)
        self.assertIn("Mirobod", labels)

    def test_help_keyboard_includes_message_admin_button(self):
        keyboard = get_help_keyboard("uz")
        callbacks = [
            button.callback_data
            for row in keyboard.inline_keyboard
            for button in row
            if button.callback_data
        ]

        self.assertIn("help_message_admin", callbacks)

    def test_profile_approval_keyboard_has_approve_and_reject(self):
        keyboard = get_profile_approval_keyboard("uz", 42)
        callbacks = [
            button.callback_data
            for row in keyboard.inline_keyboard
            for button in row
            if button.callback_data
        ]

        self.assertIn("approve_profile_42", callbacks)
        self.assertIn("reject_profile_42", callbacks)

    def test_manage_admins_keyboard_lists_admins_and_add_button(self):
        keyboard = get_manage_admins_keyboard("uz", [(111, "Ali"), (222, "Vali")])
        callbacks = [
            button.callback_data
            for row in keyboard.inline_keyboard
            for button in row
            if button.callback_data
        ]

        self.assertIn("admin_remove_111", callbacks)
        self.assertIn("admin_remove_222", callbacks)
        self.assertIn("admin_add_new", callbacks)

    def test_manage_admins_keyboard_with_no_admins_still_has_add_button(self):
        keyboard = get_manage_admins_keyboard("uz", [])
        callbacks = [
            button.callback_data
            for row in keyboard.inline_keyboard
            for button in row
            if button.callback_data
        ]

        self.assertEqual(callbacks, ["admin_add_new"])


if __name__ == "__main__":
    unittest.main()
