import discord
from discord.ext import commands #imports the commands extension
import logging
from dotenv import load_dotenv #functionality to load environment variables
import os

load_dotenv() #loads the environment var
token = os.getenv('BOT_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w') #used for logging to a file
intents = discord.Intents.default()

intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='.', intents=intents) #creates an instance of the bot

#EVENT HANDLERS
@bot.event
async def on_ready():
    print("The bot is locked in, "+bot.user.name)

@bot.event
async def on_member_join(member):
    await member.send(f"Hello, {member.name}, welcome to the {discord.Guild}!")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if "vylo" == message.content:
        await message.add_reaction("✅")
        await message.channel.send(f"{message.author.mention}, Vylo is online and functional.")
    await bot.process_commands(message) #mandatory to use to ensure the command functions are still processed

#COMMANDS
@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello, {ctx.author.mention}!")

@bot.command()
async def assign(ctx, target_member: discord.Member, target_role: str):
    role = discord.utils.get(ctx.guild.roles, name=target_role)
    if role:
        await target_member.add_roles(role)
        await ctx.send(f"{role} has been assigned to {target_member.mention}")
    else:
        await ctx.send("No such role exists!")

@bot.command()
async def unassign(ctx, target_member: discord.Member, target_role: str):
    role = discord.utils.get(ctx.guild.roles, name=target_role)
    if role:
        await target_member.remove_roles(role)
        await ctx.send(f"{role} has been removed from {target_member.mention}")
    else:
        await ctx.send("No such role exists!")



bot.run(token, log_handler=handler, log_level=logging.DEBUG) #EXECUTES THE BOT

