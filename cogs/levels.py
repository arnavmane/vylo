import discord
from discord.ext import commands
import random
import time
import datetime

class Levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.xp_cooldown = 60 # seconds

    def get_xp_for_level(self, level):
        """Standard formula for XP required for a given level"""
        return 5 * (level ** 2) + (50 * level) + 100

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        # Check if Levelling module is enabled
        if not await self.bot.db.is_module_enabled(message.guild.id, "levels"):
            return

        user_data = await self.bot.db.get_user_level(message.author.id, message.guild.id)
        last_xp_time = user_data['last_xp_time']
        current_time = time.time()

        if last_xp_time is None or current_time - last_xp_time >= self.xp_cooldown:
            xp_gain = random.randint(15, 25)
            new_xp = user_data['xp'] + xp_gain
            current_level = user_data['level']
            
            xp_needed = self.get_xp_for_level(current_level)
            
            if new_xp >= xp_needed:
                current_level += 1
                new_xp -= xp_needed
                await message.channel.send(f"GG {message.author.mention}, you just advanced to **Level {current_level}**! 🎉")

            await self.bot.db.update_user_level(
                message.author.id, 
                message.guild.id, 
                new_xp, 
                current_level, 
                current_time
            )

    @commands.command(aliases=['level', 'xp'])
    async def rank(self, ctx, member: discord.Member = None):
        """Check your current rank and XP status"""
        member = member or ctx.author
        user_data = await self.bot.db.get_user_level(member.id, ctx.guild.id)
        
        xp = user_data['xp']
        level = user_data['level']
        xp_needed = self.get_xp_for_level(level)
        
        # Calculate progress bar
        progress = int((xp / xp_needed) * 10)
        bar = "▰" * progress + "▱" * (10 - progress)

        embed = discord.Embed(
            title=f"Rank — {member.display_name}",
            color=0x2B2D31
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Level", value=f"**{level}**", inline=True)
        embed.add_field(name="Experience", value=f"{xp} / {xp_needed} XP", inline=True)
        embed.add_field(name="Progress", value=f"{bar} ({int((xp/xp_needed)*100)}%)", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(aliases=['lb', 'top'])
    async def leaderboard(self, ctx):
        """View the top members in the server"""
        leaderboard_data = await self.bot.db.get_leaderboard(ctx.guild.id)
        
        if not leaderboard_data:
            return await ctx.send("No one has earned any XP yet!")

        embed = discord.Embed(
            title=f"Leaderboard — {ctx.guild.name}",
            color=0x2B2D31,
            timestamp=datetime.datetime.utcnow()
        )
        
        description = ""
        for i, entry in enumerate(leaderboard_data, 1):
            user = self.bot.get_user(entry['user_id'])
            user_name = user.name if user else f"Unknown User ({entry['user_id']})"
            
            medal = ""
            if i == 1: medal = "🥇 "
            elif i == 2: medal = "🥈 "
            elif i == 3: medal = "🥉 "
            else: medal = f"#{i} "
            
            description += f"{medal} **{user_name}** • Lvl {entry['level']} ({entry['xp']} XP)\n"

        embed.description = description
        embed.set_footer(text="Keep chatting to climb the ranks!")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Levels(bot))
