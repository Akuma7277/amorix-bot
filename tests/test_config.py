import asyncio
import os
import tempfile
import unittest
from unittest.mock import patch

from config import build_database_url, parse_admin_ids
from bot import acquire_polling_lock
from engine import _database_host_is_resolvable


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

    def test_database_host_resolution_detects_unresolvable_host(self):
        with patch("engine.socket.getaddrinfo", side_effect=OSError):
            self.assertFalse(
                _database_host_is_resolvable("postgresql+asyncpg://user:pass@no-such-host:5432/db")
            )

    def test_acquire_polling_lock_reuses_a_single_lock_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = os.path.join(tmpdir, "bot.lock")
            acquired_first, token_first = asyncio.run(acquire_polling_lock(None, "test-lock", lock_path))
            acquired_second, token_second = asyncio.run(acquire_polling_lock(None, "test-lock", lock_path))

            self.assertTrue(acquired_first)
            self.assertTrue(token_first)
            self.assertFalse(acquired_second)
            self.assertIsNone(token_second)


if __name__ == "__main__":
    unittest.main()
