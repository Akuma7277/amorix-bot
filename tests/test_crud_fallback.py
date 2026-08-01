import unittest
from unittest.mock import patch

import crud


class BrokenSessionMaker:
    def __call__(self):
        return self

    async def __aenter__(self):
        raise OSError("db down")

    async def __aexit__(self, exc_type, exc, tb):
        return False


class CrudFallbackTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_user_by_telegram_id_returns_none_when_db_is_unavailable(self):
        with patch.object(crud, "async_session_maker", BrokenSessionMaker()):
            user = await crud.get_user_by_telegram_id(123)

        self.assertIsNone(user)


if __name__ == "__main__":
    unittest.main()
