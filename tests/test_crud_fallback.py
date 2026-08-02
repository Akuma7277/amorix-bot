import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

import crud
from models import PremiumPlan


class BrokenSessionMaker:
    def __call__(self):
        return self

    async def __aenter__(self):
        raise OSError("db down")

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeUser:
    def __init__(self, premium_plan=PremiumPlan.basic, daily_likes_used=0, daily_super_likes_used=0, daily_quota_reset_at=None):
        self.id = 1
        self.premium_plan = premium_plan
        self.daily_likes_used = daily_likes_used
        self.daily_super_likes_used = daily_super_likes_used
        # Default to "now" so tests aren't affected by the automatic daily reset unless explicitly testing it.
        self.daily_quota_reset_at = daily_quota_reset_at or datetime.now()
        self.boost_active_until = None


class FakeQuotaSession:
    def __init__(self, user):
        self.user = user

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, model, ident):
        return self.user

    async def commit(self):
        return None


class FakeQuotaSessionMaker:
    def __init__(self, user):
        self.user = user

    def __call__(self):
        return FakeQuotaSession(self.user)


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

    async def test_basic_user_blocked_after_daily_like_limit(self):
        user = FakeUser(premium_plan=PremiumPlan.basic, daily_likes_used=crud.DAILY_LIKE_LIMITS[PremiumPlan.basic])
        with patch.object(crud, "async_session_maker", FakeQuotaSessionMaker(user)):
            allowed, remaining = await crud.check_and_consume_like_quota(1, is_super_like=False)

        self.assertFalse(allowed)
        self.assertEqual(remaining, 0)

    async def test_gold_user_like_quota_decrements_remaining(self):
        user = FakeUser(premium_plan=PremiumPlan.gold, daily_likes_used=0)
        with patch.object(crud, "async_session_maker", FakeQuotaSessionMaker(user)):
            allowed, remaining = await crud.check_and_consume_like_quota(1, is_super_like=False)

        self.assertTrue(allowed)
        self.assertEqual(remaining, crud.DAILY_LIKE_LIMITS[PremiumPlan.gold] - 1)

    async def test_platinum_user_has_unlimited_likes(self):
        user = FakeUser(premium_plan=PremiumPlan.platinum, daily_likes_used=10_000)
        with patch.object(crud, "async_session_maker", FakeQuotaSessionMaker(user)):
            allowed, remaining = await crud.check_and_consume_like_quota(1, is_super_like=False)

        self.assertTrue(allowed)
        self.assertIsNone(remaining)

    async def test_basic_user_cannot_super_like(self):
        user = FakeUser(premium_plan=PremiumPlan.basic)
        with patch.object(crud, "async_session_maker", FakeQuotaSessionMaker(user)):
            allowed, remaining = await crud.check_and_consume_like_quota(1, is_super_like=True)

        self.assertFalse(allowed)
        self.assertEqual(remaining, 0)

    async def test_quota_resets_after_a_new_day(self):
        yesterday = datetime.now() - timedelta(days=1)
        user = FakeUser(premium_plan=PremiumPlan.basic, daily_likes_used=999, daily_quota_reset_at=yesterday)
        with patch.object(crud, "async_session_maker", FakeQuotaSessionMaker(user)):
            allowed, remaining = await crud.check_and_consume_like_quota(1, is_super_like=False)

        self.assertTrue(allowed)
        self.assertEqual(remaining, crud.DAILY_LIKE_LIMITS[PremiumPlan.basic] - 1)


if __name__ == "__main__":
    unittest.main()
