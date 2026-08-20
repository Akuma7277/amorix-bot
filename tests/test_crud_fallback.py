import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

import crud
from models import PremiumPlan, UserStatus


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


class _ScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class FakeLookupSession:
    def __init__(self, user):
        self.user = user

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def execute(self, query):
        return _ScalarResult(self.user)


class FakeLookupSessionMaker:
    def __init__(self, user):
        self.user = user

    def __call__(self):
        return FakeLookupSession(self.user)


class FakeAdminUser:
    def __init__(self, is_admin=False):
        self.id = 5
        self.telegram_id = 555
        self.is_admin = is_admin


class FakeBannableUser:
    def __init__(self, status=UserStatus.active, banned_until=None):
        self.id = 9
        self.telegram_id = 999
        self.status = status
        self.banned_until = banned_until


class FakeExistingUser:
    def __init__(self):
        self.id = 42
        self.telegram_id = 555111
        self.name = "Old Name"
        self.age = 20
        self.gender = None
        self.looking_for = None
        self.city = None
        self.district = None
        self.bio = None
        self.interests = None
        self.language = None
        self.status = UserStatus.inactive
        self.profile_approval_status = "rejected"


class FakeUpsertSession:
    def __init__(self, existing_user):
        self.existing_user = existing_user
        self.added = []
        self.executed_queries = []
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def execute(self, query):
        self.executed_queries.append(query)
        return _ScalarResult(self.existing_user)

    def add(self, instance):
        self.added.append(instance)
        if getattr(instance, "id", None) is None:
            instance.id = len(self.added) + 100

    async def flush(self):
        return None

    async def commit(self):
        self.committed = True

    async def refresh(self, instance):
        return None


class FakeUpsertSessionMaker:
    def __init__(self, existing_user):
        self.existing_user = existing_user
        self.session = None

    def __call__(self):
        self.session = FakeUpsertSession(self.existing_user)
        return self.session


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

    async def test_is_admin_user_true_for_env_admin_even_when_db_is_down(self):
        with patch.object(crud, "ADMIN_IDS", [999]), patch.object(crud, "async_session_maker", BrokenSessionMaker()):
            result = await crud.is_admin_user(999)

        self.assertTrue(result)

    async def test_is_admin_user_false_when_not_admin_and_db_unavailable(self):
        with patch.object(crud, "ADMIN_IDS", [999]), patch.object(crud, "async_session_maker", BrokenSessionMaker()):
            result = await crud.is_admin_user(123)

        self.assertFalse(result)

    async def test_is_admin_user_true_for_db_flagged_admin(self):
        user = FakeAdminUser(is_admin=True)
        with patch.object(crud, "ADMIN_IDS", []), patch.object(crud, "async_session_maker", FakeLookupSessionMaker(user)):
            result = await crud.is_admin_user(555)

        self.assertTrue(result)

    async def test_is_admin_user_false_for_regular_registered_user(self):
        user = FakeAdminUser(is_admin=False)
        with patch.object(crud, "ADMIN_IDS", []), patch.object(crud, "async_session_maker", FakeLookupSessionMaker(user)):
            result = await crud.is_admin_user(555)

        self.assertFalse(result)

    async def test_ban_user_with_duration_sets_future_banned_until(self):
        user = FakeBannableUser()
        with patch.object(crud, "async_session_maker", FakeQuotaSessionMaker(user)):
            result = await crud.ban_user_with_duration(user.id, 7)

        self.assertTrue(result)
        self.assertEqual(user.status, UserStatus.banned)
        self.assertGreater(user.banned_until, datetime.now() + timedelta(days=6))

    async def test_ban_user_with_duration_none_is_permanent(self):
        user = FakeBannableUser()
        with patch.object(crud, "async_session_maker", FakeQuotaSessionMaker(user)):
            result = await crud.ban_user_with_duration(user.id, None)

        self.assertTrue(result)
        self.assertEqual(user.status, UserStatus.banned)
        self.assertIsNone(user.banned_until)

    async def test_lift_user_ban_clears_status_and_duration(self):
        user = FakeBannableUser(status=UserStatus.banned, banned_until=datetime.now() + timedelta(days=1))
        with patch.object(crud, "async_session_maker", FakeQuotaSessionMaker(user)):
            result = await crud.lift_user_ban(user.id)

        self.assertTrue(result)
        self.assertEqual(user.status, UserStatus.active)
        self.assertIsNone(user.banned_until)

    async def test_auto_lift_expired_ban_leaves_active_user_untouched(self):
        user = FakeBannableUser(status=UserStatus.active)
        result = await crud.auto_lift_expired_ban(user)

        self.assertIs(result, user)
        self.assertEqual(result.status, UserStatus.active)

    async def test_auto_lift_expired_ban_leaves_future_ban_untouched(self):
        user = FakeBannableUser(status=UserStatus.banned, banned_until=datetime.now() + timedelta(days=1))
        result = await crud.auto_lift_expired_ban(user)

        self.assertEqual(result.status, UserStatus.banned)
        self.assertIsNotNone(result.banned_until)

    async def test_auto_lift_expired_ban_lifts_a_past_due_ban(self):
        user = FakeBannableUser(status=UserStatus.banned, banned_until=datetime.now() - timedelta(days=1))
        with patch.object(crud, "async_session_maker", FakeQuotaSessionMaker(user)):
            result = await crud.auto_lift_expired_ban(user)

        self.assertEqual(result.status, UserStatus.active)
        self.assertIsNone(result.banned_until)

    async def test_create_user_profile_updates_existing_user_instead_of_duplicating(self):
        existing = FakeExistingUser()
        maker = FakeUpsertSessionMaker(existing)
        with patch.object(crud, "async_session_maker", maker):
            result = await crud.create_user_profile(existing.telegram_id, {
                "name": "New Name",
                "age": 25,
                "gender": "male",
                "looking_for": "female",
                "region": "Andijon",
                "city": "Andijon",
                "district": "Markaz",
                "bio": "hi",
                "interests": ["music"],
                "language": "uz",
                "photos": ["file1"],
            })

        # Same DB identity is preserved instead of a duplicate/new row being created.
        self.assertIs(result, existing)
        self.assertEqual(result.id, 42)
        self.assertEqual(result.name, "New Name")
        # Re-registering resets moderation state so the profile goes through approval again.
        self.assertEqual(result.status, UserStatus.pending_approval)
        self.assertEqual(result.profile_approval_status, "pending")
        self.assertTrue(maker.session.committed)

    async def test_create_user_profile_falls_back_to_region_when_city_missing(self):
        # "Toshkent shahri" skips the separate city-selection step, so only "region" is ever set.
        maker = FakeUpsertSessionMaker(None)
        with patch.object(crud, "async_session_maker", maker):
            result = await crud.create_user_profile(777, {
                "name": "Ali",
                "age": 22,
                "gender": "male",
                "looking_for": "female",
                "region": "Toshkent shahri",
                "district": "Yunusobod",
                "bio": "",
                "interests": [],
                "language": "uz",
                "photos": [],
            })

        self.assertIsNotNone(result)
        self.assertEqual(result.city, "Toshkent shahri")

    async def test_create_user_profile_returns_none_when_db_is_unavailable(self):
        with patch.object(crud, "async_session_maker", BrokenSessionMaker()):
            result = await crud.create_user_profile(777, {
                "name": "Ali",
                "age": 22,
                "gender": "male",
                "looking_for": "female",
                "region": "Andijon",
                "district": "Markaz",
                "bio": "",
                "interests": [],
                "language": "uz",
                "photos": [],
            })

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
