import unittest

from inline import get_admin_dashboard_keyboard, get_search_keyboard


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


if __name__ == "__main__":
    unittest.main()
