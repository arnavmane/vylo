import discord
from discord.ext import commands
import datetime

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bad_words = ["idiot", "silly", "dumb"]

    async def log_event(self, guild_id, title: str, description: str, color):
        """Send a log embed to the configured log channel"""
        settings = await self.bot.db.get_guild_settings(guild_id)
        # Check if logging is enabled
        if not settings or not settings['logging_enabled']:
            return

        log_channel_id = settings['log_channel_id']
        if log_channel_id:
            log_channel = self.bot.get_channel(log_channel_id)
            if log_channel:
                embed = discord.Embed(
                    title=title,
                    description=description,
                    color=color,
                    timestamp=datetime.datetime.utcnow()  
                )
                await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.tree.sync()
        print(f"The bot is locked in, {self.bot.user.name}")
        await self.bot.db.create_tables()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Welcome Message
        settings = await self.bot.db.get_guild_settings(member.guild.id)
        if settings and settings['welcome_enabled']:
            embed = discord.Embed(
                title=f"Welcome to {member.guild.name}!",
                description=f"Hello {member.mention}, we are glad to have you here!",
                color=discord.Color.blue(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="About our Levelling System", value="Earn XP by chatting in the server! Use `.rank` to check your level and `.leaderboard` to see who's at the top.", inline=False)
            embed.set_footer(text=f"Server ID: {member.guild.id}")
            
            try:
                await member.send(embed=embed)
            except discord.Forbidden:
                # Log if DM fails
                await self.log_event(member.guild.id, "Welcome DM Failed", f"Could not send welcome DM to {member.mention} (DMs closed).", discord.Color.orange())
            
        await self.log_event(member.guild.id, "Member Joined", f"✅ {member.mention} joined the server.", discord.Color.green())

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self.log_event(member.guild.id, "Member Left", f"{member.mention} left the server.", discord.Color.red())

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot: return
        await self.log_event(
            message.guild.id,
            "Message Deleted",
            f"**Author:** {message.author}\n**Channel:** {message.channel.mention}\n**Content:** {message.content}",
            discord.Color.red()
        )

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot: return
        await self.log_event(
            before.guild.id,
            "Message Edited",
            f"**Author:** {before.author}\n**Channel:** {before.channel.mention}\n**Before:** {before.content}\n**After:** {after.content}",
            discord.Color.yellow()
        )

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        changes = []

        if before.timed_out_until != after.timed_out_until:
            if after.timed_out_until:
                changes.append(f"Timed out until {after.timed_out_until}")
            else:
                changes.append("Timeout removed")

        if before.nick != after.nick:
            old_nick = before.nick or before.name
            new_nick = after.nick or after.name
            changes.append(f"Nickname changed from **{old_nick}** to **{new_nick}**")

        if changes:
            description = f"Member: {after.mention}\n" + "\n".join(changes)
            await self.log_event(after.guild.id, "Member Updated", description, discord.Color.blue())

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        # Word Filter (Assuming 'warnings' module controls this as well)
        if await self.bot.db.is_module_enabled(message.guild.id, "warnings"):
            for word in self.bad_words:
                if word.lower() in message.content.lower():
                    await message.delete()
                    await message.channel.send(f"{message.author.mention}, this word is not allowed!")
                    warning_counter = await self.bot.db.add_warning(message.author.id, message.guild.id)
                    if warning_counter >= 3:
                        duration = datetime.timedelta(minutes=1)
                        await message.author.timeout(duration, reason="Repeated profanity")
                        await message.channel.send(f"{message.author.mention} has been timed out for 1 minute!")
                    return

        if "vylo" == message.content:
            await message.add_reaction("✅")
            await message.channel.send(f"{message.author.mention}, Vylo is online and functional.")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return # Ignore unknown commands

        if isinstance(error, commands.MemberNotFound):
            embed = discord.Embed(title="Error", description=f"❌ Could not find member: `{error.argument}`", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.RoleNotFound):
            embed = discord.Embed(title="Error", description=f"❌ Could not find role: `{error.argument}`", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.ChannelNotFound):
            embed = discord.Embed(title="Error", description=f"❌ Could not find channel: `{error.argument}`", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(title="Error", description=f"❌ Missing required argument: `{error.param.name}`", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.MissingPermissions):
            perms = ", ".join(error.missing_permissions)
            embed = discord.Embed(title="Error", description=f"❌ You are missing permissions: `{perms}`", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.BotMissingPermissions):
            perms = ", ".join(error.missing_permissions)
            embed = discord.Embed(title="Error", description=f"❌ I am missing permissions: `{perms}`", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(title="Error", description=f"❌ This command is on cooldown. Try again in `{error.retry_after:.2f}`s.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.CheckFailure):
            embed = discord.Embed(title="Error", description=f"❌ {error}", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.BadArgument):
            embed = discord.Embed(title="Error", description=f"❌ Invalid argument provided: {error}", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.CommandInvokeError):
            if isinstance(error.original, discord.Forbidden):
                embed = discord.Embed(
                    title="Error: Missing Permissions", 
                    description="❌ I don't have permission to do that! This usually means:\n"
                                "1. The role is **higher** than my highest role.\n"
                                "2. I don't have the **Manage Roles** permission.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

        # Log other errors
        print(f"Unhandled error in command '{ctx.command}': {error}")
        import traceback
        traceback.print_exception(type(error), error, error.__traceback__)

async def setup(bot):
    await bot.add_cog(Events(bot))
