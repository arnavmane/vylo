import discord
from discord.ext import commands
import datetime
import aiohttp

EMBED_COLOR = 0x2B2D31

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def create_embed(self, title, description):
        return discord.Embed(title=title, description=description, color=EMBED_COLOR)

    async def fetch_json(self, url):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            print(f"Error fetching {url}: {e}")
        return None

    @commands.command()
    async def hello(self, ctx):
        """Say hello to the bot!"""
        await ctx.send(f"Hello, {ctx.author.mention}!")

    @commands.command(aliases=["addrole"])
    @commands.bot_has_permissions(manage_roles=True)
    async def assign(self, ctx, target_member: discord.Member, *, target_role: discord.Role):
        """Assign a role to a user"""
        await target_member.add_roles(target_role)
        embed = self.create_embed("Role Assigned", f"➕ **{target_role.name}** has been assigned to {target_member.mention}")
        await ctx.send(embed=embed)

    @commands.command(name="unassign", aliases=["removerole"])
    @commands.bot_has_permissions(manage_roles=True)
    async def unassign(self, ctx, target_member: discord.Member, *, target_role: discord.Role):
        """Remove a role from a user"""
        await target_member.remove_roles(target_role)
        embed = self.create_embed("Role Removed", f"➖ **{target_role.name}** has been removed from {target_member.mention}")
        await ctx.send(embed=embed)

    @commands.command()
    async def poll(self, ctx, *, msg):
        """Create a poll"""
        embed = discord.Embed(title=f"Poll by {ctx.author.name}", description=f"{msg}", timestamp=datetime.datetime.now(), color=EMBED_COLOR)
        poll_message = await ctx.send(embed=embed)
        await poll_message.add_reaction("👍")
        await poll_message.add_reaction("👎")

    @commands.command()
    async def serverinfo(self, ctx):
        """View server information"""
        guild = ctx.guild
        embed = discord.Embed(title=f"🏰 {guild.name}", color=EMBED_COLOR)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
        embed.add_field(name="Members", value=guild.member_count, inline=True)
        embed.add_field(name="Channels", value=len(guild.channels), inline=True)
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="Created At", value=guild.created_at.strftime("%Y-%m-%d"), inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def userinfo(self, ctx, member: discord.Member = None):
        """View user information"""
        member = member or ctx.author
        roles = [role.mention for role in member.roles if role.name != "@everyone"]
        embed = discord.Embed(title=f"👤 {member}", color=member.color or EMBED_COLOR)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Joined At", value=member.joined_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="Created At", value=member.created_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="Roles", value=", ".join(roles) if roles else "None", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def fact(self, ctx):
        """Get a random fact"""
        data = await self.fetch_json("https://api.popcat.xyz/fact")
        if data:
            embed = self.create_embed("🧠 Did you know?", data['fact'])
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=self.create_embed("Error", "I'm out of facts!"))

    @commands.command()
    async def advice(self, ctx):
        """Get some advice"""
        data = await self.fetch_json("https://api.adviceslip.com/advice")
        if data and 'slip' in data:
            embed = self.create_embed("💡 Advice", data['slip']['advice'])
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=self.create_embed("Error", "No advice for you right now!"))

    @commands.command(aliases=["log"])
    @commands.has_permissions(administrator=True)
    async def setlog(self, ctx, channel: discord.TextChannel = None):
        """Set the logging channel"""
        channel = channel or ctx.channel
        await self.bot.db.set_log_channel(ctx.guild.id, channel.id)
        embed = self.create_embed("Log Channel Set", f"📝 Log channel set to {channel.mention}")
        await ctx.send(embed=embed)

    @commands.command()
    async def report(self, ctx, member: discord.Member, *, reason):
        """Report a member to the admins"""
        await ctx.message.delete()
        embed = self.create_embed("Report Submitted", f"✅ Report submitted against **{member}**.")
        await ctx.send(embed=embed, delete_after=5)
        
        events_cog = self.bot.get_cog('Events')
        if events_cog:
             await events_cog.log_event(
                 ctx.guild.id, 
                 "🚨 User Report", 
                 f"**Reporter:** {ctx.author.mention}\n**Reported User:** {member.mention}\n**Reason:** {reason}", 
                 discord.Color.red()
             )
             
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def prefix(self, ctx, new_prefix: str):
        """Changes the bot prefix for this server"""
        if len(new_prefix) > 5:
            await ctx.send(embed=self.create_embed("Error", "❌ Prefix is too long! Keep it under 5 characters."))
            return

        await self.bot.db.update_setting(ctx.guild.id, 'prefix', new_prefix)
        embed = self.create_embed("Prefix Changed", f"✅ Prefix changed to `{new_prefix}`")
        await ctx.send(embed=embed)

    @commands.command()
    async def help(self, ctx, command_name: str = None):
        """Shows help for commands"""
        if command_name:
            cmd = self.bot.get_command(command_name)
            if not cmd:
                await ctx.send(embed=self.create_embed("Error", f"❌ Command `{ctx.prefix}{command_name}` not found!"))
                return
                
            embed = discord.Embed(title=f"🔎 Help: {cmd.name}", description=cmd.help or "No description provided.", color=EMBED_COLOR)
            if cmd.aliases:
                embed.add_field(name="Aliases", value=", ".join([f"`{ctx.prefix}{a}`" for a in cmd.aliases]), inline=False)
            
            params = []
            if cmd.clean_params:
                for key, value in cmd.clean_params.items():
                    if value.default == value.empty:
                        params.append(f"<{key}>")
                    else:
                        params.append(f"[{key}]")
            
            usage_str = f"{ctx.prefix}{cmd.name} {' '.join(params)}"
            embed.add_field(name="Usage", value=f"`{usage_str}`", inline=False)
            
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="🤖 Vylo Bot Help",
                description=f"Here are the commands you can use. Type `{ctx.prefix}help <command>` for more info.",
                color=EMBED_COLOR
            )
            
            for cog_name, cog in self.bot.cogs.items():
                commands_list = [f"`{ctx.prefix}{c.name}`" for c in cog.get_commands()]
                if commands_list:
                    embed.add_field(name=cog_name, value=", ".join(commands_list), inline=False)
            
            embed.set_footer(text=f"Type {ctx.prefix}help <command> for details | Vylo Bot")
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(General(bot))
