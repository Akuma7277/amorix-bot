import os
import unittest

from config import build_database_url, parse_admin_ids


class ConfigHelpersTests(unittest.TestCase):
    def test_build_database_url_prefers_explicit_database_url(self):
        os.environ["DATABASE_URL"] = "postgresql+asyncpg://user:pass@host:5432/db"
        self.assertEqual(build_database_url(), "postgresql+asyncpg://user:pass@host:5432/db")

    def test_build_database_url_from_postgres_parts(self):
        os.environ.pop("DATABASE_URL", None)
        os.environ["POSTGRES_USER"] = "postgres"
        os.environ["POSTGRES_PASSWORD"] = "secret"
        os.environ["POSTGRES_HOST"] = "db.internal"
        os.environ["POSTGRES_PORT"] = "5433"
        os.environ["POSTGRES_DB"] = "amorix"

        self.assertEqual(
            build_database_url(),
            "postgresql+asyncpg://postgres:secret@db.internal:5433/amorix",
        )

    def test_parse_admin_ids(self):
        self.assertEqual(parse_admin_ids("12, 34,56"), [12, 34, 56])


if __name__ == "__main__":
    unittest.main()
