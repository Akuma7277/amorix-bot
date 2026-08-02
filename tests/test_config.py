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
        os.environ["POSTGRES_DB"] = "kairyx"

        self.assertEqual(
            build_database_url(),
            "postgresql+asyncpg://postgres:secret@db.internal:5433/kairyx",
        )

    def test_build_database_url_uses_pghost_when_present(self):
        os.environ.pop("DATABASE_URL", None)
        os.environ.pop("POSTGRES_HOST", None)
        os.environ.pop("POSTGRES_PORT", None)
        os.environ.pop("POSTGRES_USER", None)
        os.environ.pop("POSTGRES_PASSWORD", None)
        os.environ.pop("POSTGRES_DB", None)
        os.environ["PGHOST"] = "railway.internal"
        os.environ["PGPORT"] = "5433"
        os.environ["PGUSER"] = "pguser"
        os.environ["PGPASSWORD"] = "secret"
        os.environ["PGDATABASE"] = "kairyx"

        self.assertEqual(
            build_database_url(),
            "postgresql+asyncpg://pguser:secret@railway.internal:5433/kairyx",
        )

    def test_parse_admin_ids(self):
        self.assertEqual(parse_admin_ids("12, 34,56"), [12, 34, 56])


if __name__ == "__main__":
    unittest.main()
