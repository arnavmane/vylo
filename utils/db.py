import aiosqlite
import json

class DatabaseManager:
    def __init__(self, db_name="vylo.db"):
        self.db_name = db_name

    async def create_tables(self):
        async with aiosqlite.connect(self.db_name) as db:
            # Users/Warnings table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER,
                    guild_id INTEGER,
                    warning_count INTEGER DEFAULT 0,
                    PRIMARY KEY(user_id, guild_id)
                )
            """)
            
            # Guild Setttings
            # Expanded schema
            await db.execute("""
                CREATE TABLE IF NOT EXISTS guild_settings (
                    guild_id INTEGER PRIMARY KEY,
                    log_channel_id INTEGER,
                    logging_enabled BOOLEAN DEFAULT 0,
                    welcome_enabled BOOLEAN DEFAULT 0,
                    welcome_channel_id INTEGER,
                    autorole_enabled BOOLEAN DEFAULT 0,
                    autorole_role_id INTEGER,
                    prefix TEXT DEFAULT '.',
                    disabled_modules TEXT DEFAULT '[]' 
                )
            """)
            
            # Bad Words
            await db.execute("""
                CREATE TABLE IF NOT EXISTS bad_words (
                    guild_id INTEGER,
                    word TEXT,
                    PRIMARY KEY(guild_id, word)
                )
            """)

            # Levels table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS levels (
                    user_id INTEGER,
                    guild_id INTEGER,
                    xp INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 0,
                    last_xp_time TIMESTAMP,
                    PRIMARY KEY(user_id, guild_id)
                )
            """)
            
            await db.commit()

    async def get_warnings(self, user_id, guild_id):
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute("SELECT warning_count FROM users WHERE user_id = ? AND guild_id = ?", (user_id, guild_id)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 0

    async def add_warning(self, user_id, guild_id):
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute("SELECT warning_count FROM users WHERE user_id = ? AND guild_id = ?", (user_id, guild_id)) as cursor:
                result = await cursor.fetchone()
                
            if result is None:
                await db.execute("INSERT INTO users (user_id, guild_id, warning_count) VALUES (?, ?, 1)", (user_id, guild_id))
                new_count = 1
            else:
                new_count = result[0] + 1
                await db.execute("UPDATE users SET warning_count = ? WHERE user_id = ? AND guild_id = ?", (new_count, user_id, guild_id))
            
            await db.commit()
            return new_count

    # Settings Methods

    async def get_guild_settings(self, guild_id):
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM guild_settings WHERE guild_id = ?", (guild_id,)) as cursor:
                result = await cursor.fetchone()
                if result:
                    return dict(result)
                return None

    async def ensure_guild_settings(self, guild_id):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute("INSERT OR IGNORE INTO guild_settings (guild_id) VALUES (?)", (guild_id,))
            await db.commit()

    async def update_setting(self, guild_id, setting, value):
        await self.ensure_guild_settings(guild_id)
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(f"UPDATE guild_settings SET {setting} = ? WHERE guild_id = ?", (value, guild_id))
            await db.commit()

    async def get_prefix(self, guild_id):
        settings = await self.get_guild_settings(guild_id)
        return settings['prefix'] if settings else "."

    async def get_log_channel(self, guild_id):
        settings = await self.get_guild_settings(guild_id)
        if settings and settings['logging_enabled']:
           return settings['log_channel_id']
        return None

    async def set_log_channel(self, guild_id, channel_id):
        await self.ensure_guild_settings(guild_id)
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute("UPDATE guild_settings SET log_channel_id = ?, logging_enabled = 1 WHERE guild_id = ?", (channel_id, guild_id))
            await db.commit()
    
    # Helper to check if a module is enabled
    async def is_module_enabled(self, guild_id, module_name):
        settings = await self.get_guild_settings(guild_id)
        if not settings: return True # Default to enabled if no settings
        
        disabled = json.loads(settings['disabled_modules'])
        return module_name not in disabled

    async def toggle_module(self, guild_id, module_name, enable: bool):
        await self.ensure_guild_settings(guild_id)
        settings = await self.get_guild_settings(guild_id)
        disabled = json.loads(settings['disabled_modules'])
        
        if enable:
            if module_name in disabled:
                disabled.remove(module_name)
        else:
            if module_name not in disabled:
                disabled.append(module_name)
                
        await self.update_setting(guild_id, 'disabled_modules', json.dumps(disabled))

    # Leveling System Methods

    async def get_user_level(self, user_id, guild_id):
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT xp, level, last_xp_time FROM levels WHERE user_id = ? AND guild_id = ?", (user_id, guild_id)) as cursor:
                result = await cursor.fetchone()
                if result:
                    return dict(result)
                return {"xp": 0, "level": 0, "last_xp_time": None}

    async def update_user_level(self, user_id, guild_id, xp, level, last_xp_time):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute("""
                INSERT INTO levels (user_id, guild_id, xp, level, last_xp_time) 
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id, guild_id) DO UPDATE SET
                    xp = excluded.xp,
                    level = excluded.level,
                    last_xp_time = excluded.last_xp_time
            """, (user_id, guild_id, xp, level, last_xp_time))
            await db.commit()

    async def get_leaderboard(self, guild_id, limit=10):
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT user_id, xp, level FROM levels 
                WHERE guild_id = ? 
                ORDER BY xp DESC LIMIT ?
            """, (guild_id, limit)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
