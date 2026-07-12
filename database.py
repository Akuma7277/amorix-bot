import aiosqlite
from datetime import datetime, timezone

from config import DB_PATH


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                full_name TEXT,
                gender TEXT,
                phone TEXT,
                region TEXT,
                district TEXT,
                age INTEGER,
                height INTEGER,
                weight INTEGER,
                bio TEXT,
                is_banned INTEGER DEFAULT 0,
                is_complete INTEGER DEFAULT 0,
                created_at TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                file_id TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user INTEGER NOT NULL,
                to_user INTEGER NOT NULL,
                created_at TEXT
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1 INTEGER NOT NULL,
                user2 INTEGER NOT NULL,
                created_at TEXT
            )
        """)
        await db.execute("""
CREATE TABLE IF NOT EXISTS chats (
    user_id INTEGER PRIMARY KEY,
    partner_id INTEGER NOT NULL
)
""")
        await db.commit()


# ---------- Foydalanuvchilar bilan ishlash ----------

async def get_user(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def is_registration_complete(telegram_id: int) -> bool:
    user = await get_user(telegram_id)
    return bool(user and user["is_complete"])


async def create_or_reset_user(telegram_id: int, username: str, full_name: str):
    """Ro'yxatdan o'tishni (qayta) boshlaganda eski ma'lumotlarni tozalaydi."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM user_photos WHERE telegram_id = ?", (telegram_id,))
        await db.execute("DELETE FROM users WHERE telegram_id = ?", (telegram_id,))
        await db.execute(
            """INSERT INTO users (telegram_id, username, full_name, is_complete, created_at)
               VALUES (?, ?, ?, 0, ?)""",
            (telegram_id, username, full_name, datetime.now(timezone.utc).isoformat()),
        )
        await db.commit()


async def update_user_field(telegram_id: int, field: str, value):
    allowed = {"gender", "phone", "region", "district", "age", "height", "weight", "bio", "is_complete", "is_banned"}
    if field not in allowed:
        raise ValueError(f"Ruxsat etilmagan maydon: {field}")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE users SET {field} = ? WHERE telegram_id = ?", (value, telegram_id))
        await db.commit()


async def add_photo(telegram_id: int, file_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO user_photos (telegram_id, file_id) VALUES (?, ?)",
            (telegram_id, file_id),
        )
        await db.commit()


async def get_photos(telegram_id: int) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT file_id FROM user_photos WHERE telegram_id = ?", (telegram_id,))
        rows = await cur.fetchall()
        return [r[0] for r in rows]


async def count_photos(telegram_id: int) -> int:
    return len(await get_photos(telegram_id))


async def ban_user(telegram_id: int):
    await update_user_field(telegram_id, "is_banned", 1)


async def unban_user(telegram_id: int):
    await update_user_field(telegram_id, "is_banned", 0)


async def get_all_active_users() -> list:
    """Broadcast uchun: bloklanmagan, ro'yxatdan to'liq o'tgan foydalanuvchilar."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT telegram_id FROM users WHERE is_banned = 0 AND is_complete = 1"
        )
        rows = await cur.fetchall()
        return [r[0] for r in rows]


async def get_users_page(offset: int, limit: int = 10) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """SELECT * FROM users WHERE is_complete = 1
               ORDER BY id DESC LIMIT ? OFFSET ?""",
            (limit, offset),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM users WHERE is_complete = 1")
        total = (await cur.fetchone())[0]

        cur = await db.execute("SELECT COUNT(*) FROM users WHERE is_complete = 1 AND gender = 'Erkak'")
        male = (await cur.fetchone())[0]

        cur = await db.execute("SELECT COUNT(*) FROM users WHERE is_complete = 1 AND gender = 'Ayol'")
        female = (await cur.fetchone())[0]

        cur = await db.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1")
        banned = (await cur.fetchone())[0]

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        cur = await db.execute(
            "SELECT COUNT(*) FROM users WHERE is_complete = 1 AND created_at LIKE ?",
            (f"{today}%",),
        )
        today_count = (await cur.fetchone())[0]

        return {
            "total": total,
            "male": male,
            "female": female,
            "banned": banned,
            "today": today_count,
        }


# ---------- Sozlamalar (masalan majburiy kanal) ----------

async def set_setting(key: str, value: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        await db.commit()


async def get_setting(key: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = await cur.fetchone()
        return row[0] if row else None


async def delete_setting(key: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM settings WHERE key = ?", (key,))
        await db.commit()

async def get_random_profile(current_user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        cur = await db.execute(
            """
            SELECT *
            FROM users
            WHERE telegram_id != ?
              AND is_complete = 1
              AND is_banned = 0
            ORDER BY RANDOM()
            LIMIT 1
            """,
            (current_user_id,),
        )

        row = await cur.fetchone()
        return dict(row) if row else None
async def add_like(from_user: int, to_user: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO likes (from_user, to_user, created_at)
            VALUES (?, ?, ?)
            """,
            (
                from_user,
                to_user,
                datetime.now(timezone.utc).isoformat()
            )
        )
        await db.commit()

async def check_match(user1: int, user2: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            SELECT id FROM likes
            WHERE from_user = ?
            AND to_user = ?
            """,
            (user2, user1)
        )

        result = await cur.fetchone()

        return result is not None


async def add_match(user1: int, user2: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO matches (user1, user2, created_at)
            VALUES (?, ?, datetime('now'))
            """,
            (user1, user2)
        )
        await db.commit()


async def add_like(from_user: int, to_user: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO likes (from_user, to_user, created_at)
            VALUES (?, ?, ?)
            """,
            (
                from_user,
                to_user,
                datetime.now(timezone.utc).isoformat()
            )
        )
        await db.commit()
async def set_chat(user_id: int, partner_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO chats (user_id, partner_id)
            VALUES (?, ?)
            """,
            (user_id, partner_id)
        )
        await db.commit()


async def get_chat_partner(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            SELECT partner_id
            FROM chats
            WHERE user_id = ?
            """,
            (user_id,)
        )

        row = await cur.fetchone()

        return row[0] if row else None