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
    get_user_management_keyboard,
    get_ban_duration_keyboard,
    get_delete_confirmation_keyboard,
    get_accept_terms_keyboard,
    get_gender_keyboard,
    get_looking_for_keyboard,
    get_region_keyboard,
    get_interests_keyboard,
    get_photo_upload_done_keyboard,
    get_back_only_keyboard,
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

    def test_user_management_keyboard_not_banned_shows_ban_and_delete(self):
        keyboard = get_user_management_keyboard("uz", 42, is_banned=False)
        callbacks = [
            button.callback_data
            for row in keyboard.inline_keyboard
            for button in row
            if button.callback_data
        ]

        self.assertIn("manage_ban_42", callbacks)
        self.assertIn("manage_delete_prompt_42", callbacks)
        self.assertNotIn("manage_unban_42", callbacks)

    def test_user_management_keyboard_banned_shows_unban_and_delete(self):
        keyboard = get_user_management_keyboard("uz", 42, is_banned=True)
        callbacks = [
            button.callback_data
            for row in keyboard.inline_keyboard
            for button in row
            if button.callback_data
        ]

        self.assertIn("manage_unban_42", callbacks)
        self.assertIn("manage_delete_prompt_42", callbacks)
        self.assertNotIn("manage_ban_42", callbacks)

    def test_ban_duration_keyboard_offers_all_durations_and_cancel(self):
        keyboard = get_ban_duration_keyboard("uz", 42)
        callbacks = [
            button.callback_data
            for row in keyboard.inline_keyboard
            for button in row
            if button.callback_data
        ]

        self.assertIn("manage_ban_apply_42_1", callbacks)
        self.assertIn("manage_ban_apply_42_7", callbacks)
        self.assertIn("manage_ban_apply_42_30", callbacks)
        self.assertIn("manage_ban_apply_42_perm", callbacks)
        self.assertIn("manage_ban_cancel_42", callbacks)

    def test_delete_confirmation_keyboard_has_confirm_and_cancel(self):
        keyboard = get_delete_confirmation_keyboard("uz", 42)
        callbacks = [
            button.callback_data
            for row in keyboard.inline_keyboard
            for button in row
            if button.callback_data
        ]

        self.assertIn("manage_delete_confirm_42", callbacks)
        self.assertIn("manage_delete_cancel_42", callbacks)

    def test_registration_keyboards_have_no_back_button_by_default(self):
        # editing.py reuses get_interests_keyboard/get_photo_upload_done_keyboard without
        # a back_callback, so they must not show a back button outside of registration.
        for keyboard in (
            get_accept_terms_keyboard("uz"),
            get_gender_keyboard("uz"),
            get_looking_for_keyboard("uz"),
            get_region_keyboard("uz"),
            get_interests_keyboard("uz"),
            get_photo_upload_done_keyboard("uz"),
        ):
            callbacks = [
                button.callback_data
                for row in keyboard.inline_keyboard
                for button in row
                if button.callback_data
            ]
            self.assertFalse(any(c.startswith("reg_back_") for c in callbacks))

    def test_registration_keyboards_append_back_button_when_requested(self):
        cases = [
            get_accept_terms_keyboard("uz", back_callback="reg_back_language"),
            get_gender_keyboard("uz", back_callback="reg_back_age"),
            get_looking_for_keyboard("uz", back_callback="reg_back_gender"),
            get_region_keyboard("uz", back_callback="reg_back_looking_for"),
            get_interests_keyboard("uz", back_callback="reg_back_district"),
            get_photo_upload_done_keyboard("uz", back_callback="reg_back_bio"),
        ]
        for keyboard in cases:
            callbacks = [
                button.callback_data
                for row in keyboard.inline_keyboard
                for button in row
                if button.callback_data
            ]
            self.assertTrue(any(c.startswith("reg_back_") for c in callbacks))

    def test_get_back_only_keyboard_has_single_back_button(self):
        keyboard = get_back_only_keyboard("uz", "reg_back_bio")
        buttons = [button for row in keyboard.inline_keyboard for button in row]

        self.assertEqual(len(buttons), 1)
        self.assertEqual(buttons[0].callback_data, "reg_back_bio")


if __name__ == "__main__":
    unittest.main()
