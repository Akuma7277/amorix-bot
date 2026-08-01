import asyncio
import os
import tempfile
import unittest

from bot import acquire_polling_lock, release_polling_lock


class PollingLockTests(unittest.TestCase):
    def test_file_lock_prevents_duplicate_instance(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = os.path.join(tmpdir, "bot.lock")

            acquired1, token1 = asyncio.run(
                acquire_polling_lock(None, "test-lock", lock_path=lock_path)
            )
            acquired2, token2 = asyncio.run(
                acquire_polling_lock(None, "test-lock", lock_path=lock_path)
            )

            self.assertTrue(acquired1)
            self.assertFalse(acquired2)
            self.assertIsNotNone(token1)
            self.assertIsNone(token2)

            asyncio.run(release_polling_lock(None, "test-lock", token1, lock_path=lock_path))


if __name__ == "__main__":
    unittest.main()
