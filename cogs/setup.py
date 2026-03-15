import discord
from discord.ext import commands
import json

class ModuleButton(discord.ui.Button):
    def __init__(self, bot, module_name, label, is_enabled):
        self.bot = bot
        self.module_name = module_name
        self.is_enabled = is_enabled
        
        # Minimalist approach: Grey for disabled, Blurple/Green for enabled
        style = discord.ButtonStyle.success if is_enabled else discord.ButtonStyle.secondary
        
        # Match embed symbols: ● for enabled, ○ for disabled
        symbol = "●" if is_enabled else "○"
        
        super().__init__(
            style=style,
            label=f"{symbol} {label}",
            custom_id=f"toggle_{module_name}",
            row=0 if module_name in ['moderation', 'muting', 'warnings'] else 1 # Organize in rows
        )

    async def callback(self, interaction: discord.Interaction):
        new_state = not self.is_enabled
        await self.bot.db.toggle_module(interaction.guild.id, self.module_name, enable=new_state)
        
        settings = await self.bot.db.get_guild_settings(interaction.guild.id)
        view = SetupView(self.bot, interaction.guild.id, settings)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)

class LoggingView(discord.ui.View):
    def __init__(self, bot, guild_id):
        super().__init__(timeout=60)
        self.bot = bot
        self.guild_id = guild_id

    @discord.ui.button(label="Auto-create #logs", style=discord.ButtonStyle.blurple)
    async def auto_create(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True)
        }
        channel = await guild.create_text_channel('logs', overwrites=overwrites)
        await self.bot.db.set_log_channel(guild.id, channel.id)
        await self.bot.db.update_setting(guild.id, 'logging_enabled', True)
        await interaction.response.send_message(f"✅ Created and set {channel.mention} as log channel.", ephemeral=True)

    @discord.ui.button(label="Disable Logging", style=discord.ButtonStyle.danger)
    async def disable_logging(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.bot.db.update_setting(self.guild_id, 'logging_enabled', False)
        await interaction.response.send_message("Logging disabled.", ephemeral=True)

class SetupView(discord.ui.View):
    def __init__(self, bot, guild_id, settings):
        super().__init__(timeout=180)
        self.bot = bot
        self.guild_id = guild_id
        self.settings = settings
        self.disabled_modules = json.loads(settings['disabled_modules'])

        # Updated labels
        self.module_info = {
            "moderation": ("Moderation", "Kick, Ban, Unban"),
            "muting": ("Muting", "Timeouts & Mutes"),
            "warnings": ("Warnings", "Warn system & Filters"),
            "channels": ("Channel Management", "Lock, Slowmode, Nuke"),
            "fun": ("Fun", "Games & Entertainment"),
            "media": ("Media", "Memes, Cats, Dogs & Images"),
            "music": ("Music", "Play, Skip, Queue (YouTube)"),
            "levels": ("Levelling", "XP, Rank & Leaderboard")
        }

        # Dynamic Button generation
        for mod_key, (mod_label, _) in self.module_info.items():
            is_enabled = mod_key not in self.disabled_modules
            self.add_item(ModuleButton(bot, mod_key, mod_label, is_enabled))

    def get_embed(self):
        prefix = self.settings['prefix']
        
        # Minimalist status indicators
        log_status = "Enabled" if self.settings['logging_enabled'] else "Disabled"
        welcome_status = "Enabled" if self.settings['welcome_enabled'] else "Disabled"
        
        # Sleek, dark color
        embed = discord.Embed(
            title="Vylo Configuration", 
            description="Manage server settings and modules.",
            color=0x2B2D31 # Dark, premium grey
        )
        
        # Row 1: Core Settings
        settings_text = (
            f"**Prefix** `{prefix}`\n"
            f"**Logging** `{log_status}`\n"
            f"**Welcome** `{welcome_status}`"
        )
        embed.add_field(name="Settings", value=settings_text, inline=True)
        
        # Row 2: Module Overview
        # Using a sleek list format
        module_text = ""
        for mod_key, (mod_label, mod_desc) in self.module_info.items():
            # Minimalist dot indicator
            indicator = "●" if mod_key not in self.disabled_modules else "○"
            # Using bold for enabled, dim for disabled (cant dim easily, so just normal)
            name_fmt = f"**{mod_label}**" if mod_key not in self.disabled_modules else f"{mod_label}"
            
            module_text += f"`{indicator}` {name_fmt} — {mod_desc}\n"
            
        embed.add_field(name="Modules", value=module_text, inline=False)
        
        # Minimal footer
        embed.set_footer(text="Vylo • System Control")
        
        return embed

    # --- ACTION BUTTONS (Row 2/3) ---

    @discord.ui.button(label="Logging", style=discord.ButtonStyle.secondary, row=2)
    async def config_logging(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Configure Logging:", view=LoggingView(self.bot, self.guild_id), ephemeral=True)

    @discord.ui.button(label="Welcome", style=discord.ButtonStyle.secondary, row=2)
    async def toggle_welcome(self, interaction: discord.Interaction, button: discord.ui.Button):
        new_state = not self.settings['welcome_enabled']
        await self.bot.db.update_setting(self.guild_id, 'welcome_enabled', new_state)
        
        self.settings = await self.bot.db.get_guild_settings(self.guild_id)
        await interaction.response.edit_message(embed=self.get_embed(), view=SetupView(self.bot, self.guild_id, self.settings))

    @discord.ui.button(label="Prefix", style=discord.ButtonStyle.secondary, row=2)
    async def change_prefix(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Enter new prefix:", ephemeral=True)
        
        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel
        
        try:
            msg = await self.bot.wait_for('message', timeout=30.0, check=check)
            new_prefix = msg.content.strip()
            if len(new_prefix) > 5:
                await interaction.followup.send("Prefix too long.", ephemeral=True)
                return
            
            await self.bot.db.update_setting(self.guild_id, 'prefix', new_prefix)
            await interaction.followup.send(f"Prefix set to `{new_prefix}`", ephemeral=True)
        except:
            pass

class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setup(self, ctx):
        await self.bot.db.ensure_guild_settings(ctx.guild.id)
        settings = await self.bot.db.get_guild_settings(ctx.guild.id)
        
        view = SetupView(self.bot, ctx.guild.id, settings)
        await ctx.send(embed=view.get_embed(), view=view)

async def setup(bot):
    await bot.add_cog(Setup(bot))
