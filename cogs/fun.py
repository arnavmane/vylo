import discord
from discord.ext import commands
import random
import aiohttp
import html
import asyncio

EMBED_COLOR = 0x2B2D31

class Fun(commands.Cog):
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
    async def joke(self, ctx):
        """Tell a random joke"""
        data = await self.fetch_json("https://official-joke-api.appspot.com/random_joke")
        if data:
            embed = self.create_embed("😂 Joke", f"**{data['setup']}**\n\n||{data['punchline']}||")
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=self.create_embed("Error", "Couldn't think of a joke rn!"))

    @commands.command()
    async def quote(self, ctx):
        """Get an inspirational quote"""
        data = await self.fetch_json("https://zenquotes.io/api/random")
        if data and len(data) > 0:
            embed = self.create_embed("📜 Quote", f"*\"{data[0]['q']}\"*\n\n— **{data[0]['a']}**")
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=self.create_embed("Error", "Couldn't find a quote!"))

    @commands.command()
    async def roast(self, ctx, member: discord.Member = None):
        """Roast a member"""
        member = member or ctx.author
        roasts = [
            "You're like a cloud. When you disappear, it's a beautiful day.",
            "I'd agree with you but then we'd both be wrong.",
            "You bring everyone so much joy when you leave the room.",
            "Your secrets are safe with me. I never even listen when you tell me them.",
            "You're the reason this country has to put directions on shampoo.",
            "I'd give you a nasty look but you've already got one.",
            "Someday you'll go far. And I hope you stay there.",
            "Were you born on a highway? That is where most accidents happen.",
            "If laughter is the best medicine, your face must be curing the world."
        ]
        await ctx.send(f"{member.mention}, {random.choice(roasts)} 🔥")

    @commands.command()
    async def ship(self, ctx, user1: discord.Member, user2: discord.Member):
        """Calculate shipping compatibility"""
        score = random.randint(0, 100)
        emoji = "💔"
        if score > 30: emoji = "💛"
        if score > 60: emoji = "🧡"
        if score > 90: emoji = "💖"
        
        embed = discord.Embed(
            title="💗 Shipping Compatibility",
            description=f"**{user1.name}**  x  **{user2.name}**\n\nCompatibility: **{score}%** {emoji}",
            color=0xFF69B4 # Keeping Pink for Ship
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def roll(self, ctx, sides: int = 6):
        """Roll a dice (default 6 sides)"""
        result = random.randint(1, sides)
        embed = self.create_embed("🎲 Dice Roll", f"You rolled a **{result}** (1-{sides})")
        await ctx.send(embed=embed)

    @commands.command(aliases=['flip', 'coin'])
    async def coinflip(self, ctx):
        """Flip a coin"""
        result = random.choice(["Heads", "Tails"])
        embed = self.create_embed("🪙 Coin Flip", f"Result: **{result}**")
        await ctx.send(embed=embed)

    @commands.command(aliases=['8ball'])
    async def _8ball(self, ctx, *, question):
        """Ask the Magic 8-Ball"""
        responses = [
            "It is certain.", "It is decidedly so.", "Without a doubt.", "Yes definitely.",
            "You may rely on it.", "As I see it, yes.", "Most likely.", "Outlook good.",
            "Yes.", "Signs point to yes.", "Reply hazy, try again.", "Ask again later.",
            "Better not tell you now.", "Cannot predict now.", "Concentrate and ask again.",
            "Don't count on it.", "My reply is no.", "My sources say no.",
            "Outlook not so good.", "Very doubtful."
        ]
        embed = self.create_embed("🎱 Magic 8-Ball", f"**Question:** {question}\n**Answer:** {random.choice(responses)}")
        await ctx.send(embed=embed)

    @commands.command()
    async def rps(self, ctx, choice: str):
        """Play Rock, Paper, Scissors"""
        choices = ["rock", "paper", "scissors"]
        if choice.lower() not in choices:
            await ctx.send(embed=self.create_embed("Error", "Please choose rock, paper, or scissors!"))
            return

        bot_choice = random.choice(choices)
        user_choice = choice.lower()

        result = "It's a tie!"
        if (user_choice == "rock" and bot_choice == "scissors") or \
           (user_choice == "paper" and bot_choice == "rock") or \
           (user_choice == "scissors" and bot_choice == "paper"):
            result = "You win! 🎉"
        elif user_choice != bot_choice:
            result = "I win! 😈"
            
        embed = self.create_embed("Rock, Paper, Scissors", f"You chose **{user_choice}**\nI chose **{bot_choice}**\n\n**{result}**")
        await ctx.send(embed=embed)

    @commands.command()
    async def trivia(self, ctx):
        """Start a trivia question"""
        data = await self.fetch_json("https://opentdb.com/api.php?amount=1&type=multiple")
        if not data or data['response_code'] != 0:
            await ctx.send(embed=self.create_embed("Error", "Couldn't fetch a trivia question!"))
            return

        question_data = data['results'][0]
        question = html.unescape(question_data['question'])
        correct_answer = html.unescape(question_data['correct_answer'])
        answers = [html.unescape(a) for a in question_data['incorrect_answers']]
        answers.append(correct_answer)
        random.shuffle(answers)

        embed = discord.Embed(title="Trivia Time! 🧠", description=question, color=EMBED_COLOR)
        for i, ans in enumerate(answers):
            embed.add_field(name=f"Option {i+1}", value=ans, inline=True)
        
        await ctx.send(embed=embed)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()

        try:
            msg = await self.bot.wait_for('message', timeout=15.0, check=check)
            idx = int(msg.content) - 1
            if 0 <= idx < len(answers) and answers[idx] == correct_answer:
                await ctx.send(embed=self.create_embed("Correct! 🎉", f"The answer was **{correct_answer}**."))
            else:
                await ctx.send(embed=self.create_embed("Wrong! ❌", f"The correct answer was **{correct_answer}**."))
        except asyncio.TimeoutError:
            await ctx.send(embed=self.create_embed("Time's Up! ⏰", f"The answer was **{correct_answer}**."))
        except ValueError:
            pass

    @commands.command()
    async def guessnumber(self, ctx):
        """Guess the number game"""
        number = random.randint(1, 10)
        embed = self.create_embed("Guess the Number", "I'm thinking of a number between 1 and 10.")
        await ctx.send(embed=embed)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()

        try:
            msg = await self.bot.wait_for('message', timeout=10.0, check=check)
            guess = int(msg.content)
            if guess == number:
                await ctx.send(embed=self.create_embed("Correct! 🎉", f"The number was **{number}**."))
            else:
                await ctx.send(embed=self.create_embed("Wrong! ❌", f"I was thinking of **{number}**."))
        except asyncio.TimeoutError:
            await ctx.send(embed=self.create_embed("Too Slow! ⏰", f"I was thinking of **{number}**."))

async def setup(bot):
    await bot.add_cog(Fun(bot))
