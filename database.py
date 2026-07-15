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
            CREATE TABLE IF NOT EXISTS reports (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               from_user INTEGER NOT NULL,
               to_user INTEGER NOT NULL,
               reason TEXT,
               created_at TEXT
            )
        """)        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS like_views (
                user_id INTEGER PRIMARY KEY,
                offset INTEGER DEFAULT 0
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
            CREATE TABLE IF NOT EXISTS viewed_profiles (
                viewer_id INTEGER NOT NULL,
                viewed_id INTEGER NOT NULL,
                PRIMARY KEY (viewer_id, viewed_id)
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

        await db.execute("""
            CREATE TABLE IF NOT EXISTS photo_views (
                user_id INTEGER PRIMARY KEY,
                photo_index INTEGER DEFAULT 0
            )
        """)

        await db.execute("""
CREATE TABLE IF NOT EXISTS filters (
    user_id INTEGER PRIMARY KEY,
    gender TEXT,
    min_age INTEGER DEFAULT 18,
    max_age INTEGER DEFAULT 99
)
""")

        try:
            await db.execute("""
                ALTER TABLE filters
                ADD COLUMN region TEXT
            """)
        except:
            pass

        try:
            await db.execute("""
                ALTER TABLE filters
                ADD COLUMN district TEXT
            """)
        except:
            pass

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

        filter_data = await get_filter(current_user_id)

        if filter_data:
            cur = await db.execute(
                """
                SELECT *
                FROM users
                WHERE telegram_id != ?
                  AND is_complete = 1
                  AND is_banned = 0
                  AND gender = ?
                  AND age BETWEEN ? AND ?
                  AND (? IS NULL OR region = ?)
                  AND (? IS NULL OR district = ?)
                  AND telegram_id NOT IN (
                      SELECT viewed_id
                      FROM viewed_profiles
                      WHERE viewer_id = ?
                  )
                ORDER BY RANDOM()
                LIMIT 1
                """,
                (
                   current_user_id,
                   filter_data["gender"],
                   filter_data["min_age"],
                   filter_data["max_age"],
                   filter_data.get("region"),
                   filter_data.get("region"),
                   filter_data.get("district"),
                   filter_data.get("district"),
                   current_user_id,
                ),
            )
        else:
            cur = await db.execute(
                """
                SELECT *
                FROM users
                WHERE telegram_id != ?
                  AND is_complete = 1
                  AND is_banned = 0
                  AND telegram_id NOT IN (
                      SELECT viewed_id
                      FROM viewed_profiles
                      WHERE viewer_id = ?
                  )
                ORDER BY RANDOM()
                LIMIT 1
                """,
                (
                    current_user_id,
                    current_user_id,
                ),
            )

        row = await cur.fetchone()

        if row:
            await add_viewed_profile(
                current_user_id,
                row["telegram_id"]
            )
            return dict(row)

        await clear_viewed_profiles(current_user_id)

        return await get_random_profile(current_user_id)
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


async def set_message_target(user_id: int, target_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO chats(user_id, partner_id)
            VALUES (?, ?)
            """,
            (user_id, target_id)
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

async def get_photo_index(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            SELECT photo_index
            FROM photo_views
            WHERE user_id = ?
            """,
            (user_id,)
        )

        row = await cur.fetchone()

        return row[0] if row else 0


async def set_photo_index(user_id: int, index: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO photo_views
            (user_id, photo_index)
            VALUES (?, ?)
            """,
            (user_id, index)
        )

        await db.commit()


async def set_filter(
    user_id: int,
    gender: str,
    min_age: int,
    max_age: int,
    region: str = None,
    district: str = None
):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO filters
            (user_id, gender, min_age, max_age, region, district)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                gender,
                min_age,
                max_age,
                region,
                district
            )
        )

        await db.commit()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO filters
            (user_id, gender, min_age, max_age, region, district)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                gender,
                min_age,
                max_age,
                region,
                district
            )
        )

        await db.commit()
async def get_filter(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        cur = await db.execute(
            "SELECT * FROM filters WHERE user_id = ?",
            (user_id,)
        )

        row = await cur.fetchone()

        return dict(row) if row else None


async def add_viewed_profile(viewer_id: int, viewed_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO viewed_profiles
            (viewer_id, viewed_id)
            VALUES (?, ?)
            """,
            (viewer_id, viewed_id)
        )
        await db.commit()


async def clear_viewed_profiles(viewer_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            DELETE FROM viewed_profiles
            WHERE viewer_id = ?
            """,
            (viewer_id,)
        )
        await db.commit()

async def get_likes_for_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        cur = await db.execute(
            """
            SELECT users.*
            FROM likes
            JOIN users
                ON users.telegram_id = likes.from_user
            WHERE likes.to_user = ?
            ORDER BY likes.id DESC
            """,
            (user_id,)
        )

        rows = await cur.fetchall()

        return [dict(row) for row in rows]


async def get_last_like(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        cur = await db.execute(
            """
            SELECT users.*
            FROM likes
            JOIN users
                ON users.telegram_id = likes.from_user
            WHERE likes.to_user = ?
            ORDER BY likes.id DESC
            LIMIT 1
            """,
            (user_id,)
        )

        row = await cur.fetchone()

        return dict(row) if row else None
async def get_like_offset(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            SELECT offset
            FROM like_views
            WHERE user_id = ?
            """,
            (user_id,)
        )

        row = await cur.fetchone()

        return row[0] if row else 0

async def set_like_offset(user_id: int, offset: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO like_views
            (user_id, offset)
            VALUES (?, ?)
            """,
            (user_id, offset)
        )

        await db.commit()

async def add_report(from_user: int, to_user: int, reason: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO reports
            (from_user, to_user, reason, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                from_user,
                to_user,
                reason,
                datetime.now(timezone.utc).isoformat()
            )
        )
        
        await db.commit()


async def get_reports():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        cur = await db.execute("""
            SELECT
                reports.id,
                reports.from_user,
                reports.to_user,
                reports.reason,
                reports.created_at,
                u1.full_name AS from_name,
                u2.full_name AS to_name
            FROM reports
            LEFT JOIN users u1
                ON u1.telegram_id = reports.from_user
            LEFT JOIN users u2
                ON u2.telegram_id = reports.to_user
            ORDER BY reports.id DESC
        """)

        rows = await cur.fetchall()

        return [dict(row) for row in rows]