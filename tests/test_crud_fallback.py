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

    async def test_engine_fallback_session_delegates_to_real_session_when_available(self):
        class FakeSession:
            def __init__(self):
                self.added = []
                self.committed = False

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            def add(self, instance):
                self.added.append(instance)

            async def commit(self):
                self.committed = True

        class FakeSessionMaker:
            def __call__(self):
                return FakeSession()

        from engine import _FallbackSession

        session = _FallbackSession(FakeSessionMaker()())
        await session.__aenter__()
        session.add("x")
        await session.commit()

        self.assertEqual(session._real_session.added, ["x"])
        self.assertTrue(session._real_session.committed)


if __name__ == "__main__":
    unittest.main()
