import discord
from discord.ext import commands
import random
import aiohttp

EMBED_COLOR = 0x2B2D31

class Media(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    def create_embed(self, title, description=None, color=EMBED_COLOR, image_url=None):
        embed = discord.Embed(title=title, description=description, color=color)
        if image_url:
            embed.set_image(url=image_url)
        return embed

    async def get_reddit_image(self, subreddit):
        try:
            url = f"https://www.reddit.com/r/{subreddit}/hot.json"
            headers = {'User-Agent': 'python:vylo-bot:v1.0 (by /u/vylo_dev)'}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        posts = data['data']['children']
                        if not posts:
                            return None, None
                        
                        image_posts = [
                            post['data'] for post in posts 
                            if not post['data']['is_self'] 
                            and not post['data'].get('stickied', False)
                            and 'url_overridden_by_dest' in post['data']
                            and any(post['data']['url_overridden_by_dest'].endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif'])
                        ]

                        if not image_posts:
                             return None, None

                        post = random.choice(image_posts)
                        return post['url_overridden_by_dest'], post['title']
                    else:
                        print(f"Reddit API returned status: {response.status}")
                        return None, None
        except Exception as e:
            print(f"Error fetching from reddit: {e}")
            return None, None

    @commands.command()
    async def meme(self, ctx):
        """Fetch a random meme from Reddit"""
        image_url, title = await self.get_reddit_image("memes")
        if image_url:
            await ctx.send(embed=self.create_embed(title, color=EMBED_COLOR, image_url=image_url))
        else:
            await ctx.send(embed=self.create_embed("Error", "Could not fetch a meme at the moment. Try again later!"))

    @commands.command()
    async def cat(self, ctx):
        """Fetch a random cat picture"""
        image_url, title = await self.get_reddit_image("cats")
        if image_url:
            await ctx.send(embed=self.create_embed("Meow! 🐱", color=EMBED_COLOR, image_url=image_url))
        else:
            await ctx.send(embed=self.create_embed("Error", "Could not fetch a cat picture. The cats are hiding!"))

    @commands.command()
    async def dog(self, ctx):
        """Fetch a random dog picture"""
        image_url, title = await self.get_reddit_image("dogpictures")
        if image_url:
            await ctx.send(embed=self.create_embed("Woof! 🐶", color=EMBED_COLOR, image_url=image_url))
        else:
            await ctx.send(embed=self.create_embed("Error", "Could not fetch a dog picture. The dogs are out for a walk!"))

async def setup(bot):
    await bot.add_cog(Media(bot))
