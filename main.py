import discord
from discord.ext import commands
import os
import asyncio
import logging
from dotenv import load_dotenv
from utils.db import DatabaseManager
import json

# Setup Logging
logging.basicConfig(level=logging.INFO)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

async def get_prefix(bot, message):
    if not message.guild:
        return '.'
    return await bot.db.get_prefix(message.guild.id)

class VyloBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix=get_prefix, intents=intents, help_command=None)
        
        self.db = DatabaseManager()

    async def setup_hook(self):
        # Load Cogs
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
        
        # Initialize DB
        await self.db.create_tables()

    async def on_check(self, ctx):
        # Global check for disabled modules
        if not ctx.guild: return True
        
        # Map cogs/commands to module names
        # Simple mapping strat: Cog name = Module name
        cog_name = ctx.cog.qualified_name.lower() if ctx.cog else None
        
        # Explicit mapping for command groups if needed, but Cog-based is easiest for now
        # Our modules in Setup were: moderation, muting, warnings, channels, fun, media
        # Our Cogs are: Moderation, Fun, Media, General, Events, Setup
        
        module_map = {
            "kick": "moderation", "ban": "moderation", "unban": "moderation",
            "mute": "muting", "unmute": "muting",
            "warn": "warnings", "warnings": "warnings",
            "lock": "channels", "unlock": "channels", "slowmode": "channels", "nuke": "channels",
            "meme": "media", "cat": "media", "dog": "media",
            "roll": "fun", "coinflip": "fun", "joke": "fun", "quote": "fun",
            "play": "music", "skip": "music", "stop": "music", "queue": "music", "join": "music", "leave": "music",
            "rank": "levels", "level": "levels", "xp": "levels", "leaderboard": "levels", "lb": "levels", "top": "levels"
        }
        
        # If command name maps to a module, check it
        cmd_module = module_map.get(ctx.command.name)
        if cmd_module:
            is_enabled = await self.db.is_module_enabled(ctx.guild.id, cmd_module)
            if not is_enabled:
                raise commands.CheckFailure(f"Module `{cmd_module}` is disabled in this server.")
                return False

        # Fallback: Check Cog-wide disable (e.g. if 'Fun' cog maps to 'fun' module)
        if cog_name == "fun":
             if not await self.db.is_module_enabled(ctx.guild.id, "fun"):
                 raise commands.CheckFailure("Fun module is disabled.")
        
        if cog_name == "media":
             if not await self.db.is_module_enabled(ctx.guild.id, "media"):
                 raise commands.CheckFailure("Media module is disabled.")

        return True

async def main():
    bot = VyloBot()
    # verify global check is registered
    bot.add_check(bot.on_check)
    
    async with bot:
         await bot.start(TOKEN)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
