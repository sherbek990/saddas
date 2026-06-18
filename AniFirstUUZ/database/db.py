import aiosqlite
import json
from config import DB_PATH
from datetime import datetime


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Foydalanuvchilar
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                user_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                full_name TEXT,
                is_banned INTEGER DEFAULT 0,
                joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_active TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Animalar
        await db.execute("""
            CREATE TABLE IF NOT EXISTS animes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                fanadub_name TEXT,
                description TEXT,
                genre TEXT,
                status TEXT DEFAULT 'ongoing',
                poster_file_id TEXT,
                is_restricted INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Anime epizodlari
        await db.execute("""
            CREATE TABLE IF NOT EXISTS episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                anime_id INTEGER NOT NULL,
                episode_number INTEGER NOT NULL,
                title TEXT,
                video_file_id TEXT,
                thumbnail_file_id TEXT,
                duration INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (anime_id) REFERENCES animes(id) ON DELETE CASCADE
            )
        """)

        # Majburiy obuna kanallari
        await db.execute("""
            CREATE TABLE IF NOT EXISTS required_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                channel_id TEXT,
                channel_link TEXT NOT NULL,
                channel_name TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                sort_order INTEGER DEFAULT 0
            )
        """)

        # Bot sozlamalari
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bot_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Kanallar (post yuborish uchun)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS broadcast_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT UNIQUE NOT NULL,
                channel_name TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                added_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Standart sozlamalar
        defaults = [
            ("welcome_text", "🎌 Anime Botga Xush Kelibsiz!\n\nEng yaxshi anime seriallarini tomosha qiling."),
            ("subscription_required", "1"),
            ("maintenance_mode", "0"),
            ("bot_name", "Anime Bot"),
        ]
        for key, value in defaults:
            await db.execute(
                "INSERT OR IGNORE INTO bot_settings (key, value) VALUES (?, ?)",
                (key, value)
            )

        await db.commit()
    print("✅ Database tayyor!")


# ==================== USERS ====================

async def add_user(user_id: int, username: str = None, full_name: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR IGNORE INTO users (user_id, username, full_name)
            VALUES (?, ?, ?)
        """, (user_id, username, full_name))
        await db.execute("""
            UPDATE users SET last_active = CURRENT_TIMESTAMP,
            username = COALESCE(?, username),
            full_name = COALESCE(?, full_name)
            WHERE user_id = ?
        """, (username, full_name, user_id))
        await db.commit()


async def get_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_all_users(include_banned=False):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT * FROM users"
        if not include_banned:
            query += " WHERE is_banned = 0"
        async with db.execute(query) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def ban_user(user_id: int, ban: bool = True):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_banned = ? WHERE user_id = ?", (1 if ban else 0, user_id))
        await db.commit()


async def get_users_count():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users WHERE is_banned = 0") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


# ==================== ANIMES ====================

async def add_anime(title: str, fanadub_name: str = None, description: str = None,
                    genre: str = None, poster_file_id: str = None) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO animes (title, fanadub_name, description, genre, poster_file_id)
            VALUES (?, ?, ?, ?, ?)
        """, (title, fanadub_name, description, genre, poster_file_id))
        await db.commit()
        return cursor.lastrowid


async def get_anime(anime_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM animes WHERE id = ?", (anime_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_all_animes(page: int = 1, per_page: int = 10, restricted_for_admin: bool = False):
    offset = (page - 1) * per_page
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT * FROM animes"
        if not restricted_for_admin:
            query += " WHERE is_restricted = 0"
        query += f" ORDER BY created_at DESC LIMIT {per_page} OFFSET {offset}"
        async with db.execute(query) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_animes_count(include_restricted: bool = False):
    async with aiosqlite.connect(DB_PATH) as db:
        query = "SELECT COUNT(*) FROM animes"
        if not include_restricted:
            query += " WHERE is_restricted = 0"
        async with db.execute(query) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


async def update_anime(anime_id: int, **kwargs):
    if not kwargs:
        return
    set_parts = ", ".join([f"{k} = ?" for k in kwargs.keys()])
    values = list(kwargs.values()) + [anime_id]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE animes SET {set_parts}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            values
        )
        await db.commit()


async def delete_anime(anime_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM animes WHERE id = ?", (anime_id,))
        await db.commit()


async def restrict_anime(anime_id: int, restrict: bool = True):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE animes SET is_restricted = ? WHERE id = ?",
                         (1 if restrict else 0, anime_id))
        await db.commit()


# ==================== EPISODES ====================

async def add_episode(anime_id: int, episode_number: int, title: str = None,
                       video_file_id: str = None, thumbnail_file_id: str = None) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO episodes (anime_id, episode_number, title, video_file_id, thumbnail_file_id)
            VALUES (?, ?, ?, ?, ?)
        """, (anime_id, episode_number, title, video_file_id, thumbnail_file_id))
        await db.commit()
        return cursor.lastrowid


async def get_episodes(anime_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM episodes WHERE anime_id = ? ORDER BY episode_number",
            (anime_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_episode(episode_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM episodes WHERE id = ?", (episode_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def update_episode(episode_id: int, **kwargs):
    if not kwargs:
        return
    set_parts = ", ".join([f"{k} = ?" for k in kwargs.keys()])
    values = list(kwargs.values()) + [episode_id]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE episodes SET {set_parts} WHERE id = ?", values)
        await db.commit()


async def delete_episode(episode_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM episodes WHERE id = ?", (episode_id,))
        await db.commit()


# ==================== REQUIRED CHANNELS ====================

async def get_required_channels(platform: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT * FROM required_channels WHERE is_active = 1"
        params = []
        if platform:
            query += " AND platform = ?"
            params.append(platform)
        query += " ORDER BY sort_order"
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def add_required_channel(platform: str, channel_link: str, channel_name: str,
                                channel_id: str = None):
    # YouTube uchun max 2 ta cheklovi
    if platform == "youtube":
        existing = await get_required_channels("youtube")
        if len(existing) >= 2:
            return False, "YouTube uchun maksimal 2 ta kanal qo'shish mumkin!"

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO required_channels (platform, channel_id, channel_link, channel_name)
            VALUES (?, ?, ?, ?)
        """, (platform, channel_id, channel_link, channel_name))
        await db.commit()
    return True, "Kanal qo'shildi!"


async def remove_required_channel(channel_db_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM required_channels WHERE id = ?", (channel_db_id,))
        await db.commit()


async def toggle_required_channel(channel_db_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE required_channels
            SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END
            WHERE id = ?
        """, (channel_db_id,))
        await db.commit()


async def get_all_required_channels():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM required_channels ORDER BY platform, sort_order"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


# ==================== BOT SETTINGS ====================

async def get_setting(key: str, default: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT value FROM bot_settings WHERE key = ?", (key,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else default


async def set_setting(key: str, value: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO bot_settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
        """, (key, value))
        await db.commit()


async def get_all_settings():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM bot_settings") as cursor:
            rows = await cursor.fetchall()
            return {r["key"]: r["value"] for r in rows}


# ==================== BROADCAST CHANNELS ====================

async def add_broadcast_channel(channel_id: str, channel_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute("""
                INSERT INTO broadcast_channels (channel_id, channel_name)
                VALUES (?, ?)
            """, (channel_id, channel_name))
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False


async def get_broadcast_channels():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM broadcast_channels WHERE is_active = 1"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def remove_broadcast_channel(channel_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM broadcast_channels WHERE channel_id = ?", (channel_id,))
        await db.commit()
