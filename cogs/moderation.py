import discord
from discord.ext import commands
import datetime
import asyncio

# Aesthetic Color
EMBED_COLOR = 0x2B2D31

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def create_embed(self, title, description, color=EMBED_COLOR):
        embed = discord.Embed(description=description, color=color)
        embed.set_author(name=title, icon_url="https://i.imgur.com/8bfQAjA.png") # Generic shield icon or similar
        return embed

    @commands.command()
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Kick a member from the server"""
        await member.kick(reason=reason)
        embed = self.create_embed("Member Kicked", f"👢 **{member}** has been kicked.\n**Reason:** {reason}")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Ban a member from the server"""
        await member.ban(reason=reason)
        embed = self.create_embed("Member Banned", f"🔨 **{member}** has been banned.\n**Reason:** {reason}")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx, *, user):
        """Unban a user (ID or Name#Discrim)"""
        banned_users = [entry async for entry in ctx.guild.bans()]
        member_name, member_discriminator = user.split('#') if '#' in user else (user, None)
        
        for ban_entry in banned_users:
            user = ban_entry.user
            if (user.name, user.discriminator) == (member_name, member_discriminator) or str(user.id) == member_name:
                await ctx.guild.unban(user)
                embed = self.create_embed("Member Unbanned", f"🔓 **{user}** has been unbanned.")
                await ctx.send(embed=embed)
                return
        
        await ctx.send(embed=self.create_embed("Error", f"❌ Couldn't find user **{user}** in ban list."))

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def mute(self, ctx, member: discord.Member, duration: int, *, unit="m"):
        """Timeout a member (Units: s, m, h, d)"""
        if unit == "s": delta = datetime.timedelta(seconds=duration)
        elif unit == "m": delta = datetime.timedelta(minutes=duration)
        elif unit == "h": delta = datetime.timedelta(hours=duration)
        elif unit == "d": delta = datetime.timedelta(days=duration)
        else:
            await ctx.send(embed=self.create_embed("Invalid Unit", "❌ Use s, m, h, or d."))
            return
            
        await member.timeout(delta, reason=f"Muted by {ctx.author}")
        embed = self.create_embed("Member Muted", f"🔇 **{member}** has been muted for **{duration}{unit}**.")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def unmute(self, ctx, member: discord.Member):
        """Remove timeout from a member"""
        await member.timeout(None, reason=f"Unmuted by {ctx.author}")
        embed = self.create_embed("Member Unmuted", f"🔊 **{member}** has been unmuted.")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Warn a member"""
        count = await self.bot.db.add_warning(member.id, ctx.guild.id)
        embed = self.create_embed("Member Warned", f"⚠️ **{member.mention}** has been warned.\n**Reason:** {reason}\n**Total Warnings:** {count}")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def warnings(self, ctx, member: discord.Member):
        """Check warnings for a member"""
        count = await self.bot.db.get_warnings(member.id, ctx.guild.id)
        embed = self.create_embed("User Warnings", f"ℹ️ **{member.name}** has **{count}** warnings.")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def lock(self, ctx, channel: discord.TextChannel = None):
        """Lock the current or specified channel"""
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(embed=self.create_embed("Channel Locked", f"🔒 **{channel.mention}** has been locked."))

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def unlock(self, ctx, channel: discord.TextChannel = None):
        """Unlock the current or specified channel"""
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = None
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(embed=self.create_embed("Channel Unlocked", f"🔓 **{channel.mention}** has been unlocked."))

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def slowmode(self, ctx, channel: discord.TextChannel = None, seconds: int = 0):
        """Set slowmode for a channel (0 to disable)"""
        channel = channel or ctx.channel
        await channel.edit(slowmode_delay=seconds)
        await ctx.send(embed=self.create_embed("Slowmode Set", f"🐢 Slowmode for **{channel.mention}** set to **{seconds}s**."))

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def nuke(self, ctx, channel: discord.TextChannel = None):
        """Clone and delete a channel to clear all history"""
        channel = channel or ctx.channel
        await ctx.send(embed=self.create_embed("Nuking", "☢️ Nuking this channel in 5 seconds..."))
        await asyncio.sleep(5)
        new_channel = await channel.clone(reason="Nuked")
        await channel.delete()
        await new_channel.send(embed=self.create_embed("Channel Nuked", "☢️ **Channel Nuked!**"))

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int = 5):
        """Delete a number of messages"""
        if amount > 100: amount = 100
        await ctx.channel.purge(limit=amount + 1)
        await ctx.send(embed=self.create_embed("Messages Cleared", f"🧹 Cleared **{amount}** messages."), delete_after=3)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge(self, ctx, member: discord.Member, amount: int = 10):
        """Delete messages from a specific user"""
        def check(m):
            return m.author == member
        deleted = await ctx.channel.purge(limit=amount, check=check)
        await ctx.send(embed=self.create_embed("Messages Purged", f"🧹 Cleared **{len(deleted)}** messages from **{member}**."), delete_after=3)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
