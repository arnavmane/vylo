import discord
from discord.ext import commands
import asyncio
import yt_dlp
import os
from datetime import timedelta

# Suppress noise about console usage from errors
def bug_reports_message(*args, **kwargs):
    return ''
yt_dlp.utils.bug_reports_message = bug_reports_message

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

ffmpeg_options = {
    'options': '-vn',
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.uploader = data.get('uploader')
        self.duration = data.get('duration')
        self.thumbnail = data.get('thumbnail')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        
        executable = 'ffmpeg'
        if os.path.isfile('ffmpeg.exe'):
            executable = './ffmpeg.exe'
            
        return cls(discord.FFmpegPCMAudio(filename, executable=executable, **ffmpeg_options), data=data)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {} # guild_id -> list of dictionaries (title, uploader, url)

    def get_track_embed(self, player, status="Now Playing"):
        embed = discord.Embed(
            title=player.title, 
            url=player.data.get('webpage_url') or player.url,
            color=0x2B2D31 # Dark Premium Grey
        )
        embed.set_author(name=status, icon_url="https://i.imgur.com/bO3B3yP.png") # Generic music icon or bot icon
        
        uploader = player.uploader if player.uploader else "Unknown Artist"
        duration = str(timedelta(seconds=player.duration)) if player.duration else "Live"
        
        embed.add_field(name="Artist", value=uploader, inline=True)
        embed.add_field(name="Duration", value=duration, inline=True)
        
        if player.thumbnail:
            embed.set_thumbnail(url=player.thumbnail)
            
        return embed

    @commands.command()
    async def join(self, ctx):
        """Joins a voice channel"""
        if not ctx.message.author.voice:
            await ctx.send("You are not connected to a voice channel.")
            return

        channel = ctx.message.author.voice.channel
        if ctx.voice_client is not None:
             await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()

    @commands.command()
    async def play(self, ctx, *, query):
        """Plays a file from the local filesystem"""
        if not ctx.voice_client:
            await self.join(ctx)
            if not ctx.voice_client: return 
        
        async with ctx.typing():
            try:
                # We need to extract info first to get metadata for queue if we are queuing
                # But creating a player does extract info.
                
                # To avoid double extraction for queue, we might just store query and re-extract
                # OR we extract info now.
                
                player = await YTDLSource.from_url(query, loop=self.bot.loop, stream=True)
                
                if ctx.voice_client.is_playing():
                    # Queue logic
                    if ctx.guild.id not in self.queues:
                        self.queues[ctx.guild.id] = []
                        
                    # Store metadata for display
                    self.queues[ctx.guild.id].append({
                        'query': query,
                        'title': player.title,
                        'uploader': player.uploader
                    })
                    
                    embed = discord.Embed(title="Added to Queue", description=f"[{player.title}]({player.data.get('webpage_url')})", color=0x2B2D31)
                    embed.set_footer(text=f"By {player.uploader}")
                    if player.thumbnail: embed.set_thumbnail(url=player.thumbnail)
                    
                    await ctx.send(embed=embed)
                else:
                    ctx.voice_client.play(player, after=lambda e: self.check_queue(ctx))
                    await ctx.send(embed=self.get_track_embed(player))
            except Exception as e:
                await ctx.send(f"An error occurred: {e}")

    def check_queue(self, ctx):
        if ctx.guild.id in self.queues and self.queues[ctx.guild.id]:
            track_info = self.queues[ctx.guild.id].pop(0)
            asyncio.run_coroutine_threadsafe(self.play_next(ctx, track_info['query']), self.bot.loop)

    async def play_next(self, ctx, query):
        if ctx.voice_client:
            player = await YTDLSource.from_url(query, loop=self.bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: self.check_queue(ctx))
            await ctx.send(embed=self.get_track_embed(player))

    @commands.command()
    async def skip(self, ctx):
        """Skips the current song"""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏭️ **Skipped**")

    @commands.command()
    async def stop(self, ctx):
        """Stops and clears queue"""
        if ctx.guild.id in self.queues:
            self.queues[ctx.guild.id].clear()
            
        if ctx.voice_client:
             ctx.voice_client.stop()
        await ctx.send("⏹️ **Stopped and cleared queue**")

    @commands.command()
    async def queue(self, ctx):
        if ctx.guild.id in self.queues and self.queues[ctx.guild.id]:
            # Aesthetic Queue List
            desc = ""
            for i, track in enumerate(self.queues[ctx.guild.id]):
                desc += f"`{i+1}.` **{track['title']}**\n   by *{track['uploader']}*\n\n"
            
            embed = discord.Embed(title="🎶 Music Queue", description=desc, color=0x2B2D31)
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=discord.Embed(description="The queue is empty.", color=0x2B2D31))

    @commands.command()
    async def leave(self, ctx):
        """Stops and disconnects the bot from voice"""
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("👋 **Disconnected**")
            
async def setup(bot):
    await bot.add_cog(Music(bot))
