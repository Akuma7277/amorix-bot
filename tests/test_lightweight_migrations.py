import unittest

from sqlalchemy.dialects import postgresql

from bot import _build_add_column_ddl, _describe_column_default
from models import Like, User


class LightweightMigrationDDLTests(unittest.TestCase):
    def test_boolean_column_default_is_rendered_as_false(self):
        column = Like.__table__.columns["is_super_like"]
        self.assertEqual(_describe_column_default(column), " DEFAULT FALSE")

    def test_integer_column_default_is_rendered(self):
        column = User.__table__.columns["daily_likes_used"]
        self.assertEqual(_describe_column_default(column), " DEFAULT 0")

    def test_column_without_default_has_no_default_clause(self):
        column = User.__table__.columns["boost_active_until"]
        self.assertEqual(_describe_column_default(column), "")

    def test_add_column_ddl_includes_table_column_and_default(self):
        column = User.__table__.columns["daily_super_likes_used"]
        ddl = _build_add_column_ddl("users", column, postgresql.dialect())

        self.assertIn('ALTER TABLE "users" ADD COLUMN "daily_super_likes_used"', ddl)
        self.assertIn("DEFAULT 0", ddl)

    def test_add_column_ddl_for_new_premium_columns(self):
        for column_name in ("daily_likes_used", "daily_super_likes_used", "daily_quota_reset_at", "boost_active_until"):
            column = User.__table__.columns[column_name]
            ddl = _build_add_column_ddl("users", column, postgresql.dialect())
            self.assertIn(f'"{column_name}"', ddl)


if __name__ == "__main__":
    unittest.main()
