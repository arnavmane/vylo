import discord
from discord.ext import commands #imports the commands extension
import logging
from dotenv import load_dotenv #functionality to load environment variables
import os
import datetime
import sqlite3

BASE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
def create_user_table():
    connection =  sqlite3.connect(f"{BASE_DIRECTORY}\\user_warnings.db")
    cursor =  connection.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS USERS(
                   "user_id" int,
                   "guild_id" int,
                   "warning_count" int,
                   PRIMARY KEY("user_id", "guild_id"))""")
    connection.commit()
    connection.close()
create_user_table()

def get_warnings_and_inc(user_id: int, guild_id: int):
    connection =  sqlite3.connect(f"{BASE_DIRECTORY}\\user_warnings.db")
    cursor =  connection.cursor()
    cursor.execute("""SELECT warning_count FROM USERS WHERE (user_id = ?) AND (guild_id = ?);""", (user_id, guild_id))

    result = cursor.fetchone()
    if result == None:
        cursor.execute("""INSERT INTO USERS VALUES(?, ?, 1)""", (user_id, guild_id))
        connection.commit()
        connection.close()
        return 1
    
    cursor.execute("""UPDATE USERS SET warning_count = ? WHERE (user_id = ? ) AND (guild_id = ?)""", (result[0]+1, user_id, guild_id))
    connection.commit()
    connection.close()
    return result[0]+1

bad_words = ["idiot", "silly", "dumb"]

#LOGGING
async def log_event(title: str, description: str, color=discord.Color.blue()):
    """Send a log embed to the configured log channel"""
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.datetime.utcnow()  
            
        )
        await log_channel.send(embed=embed)

load_dotenv() #loads the environment var
token = os.getenv('BOT_TOKEN')
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID')) 

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w') #used for logging to a file
intents = discord.Intents.default()

intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='.', intents=intents) #creates an instance of the bot

#EVENT HANDLERS
@bot.event
async def on_ready():
    await bot.tree.sync()
    print("The bot is locked in, "+bot.user.name)

@bot.event
async def on_member_join(member):
    await member.send(f"Hello {member.name}, welcome to the {member.guild.name}!")
    await log_event("Member Joined", f"✅ {member.mention} joined the server.", discord.Color.green()) #for logging purposes

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    else:
        for words in bad_words:
            if words.lower() in message.content.lower():
                await message.delete()
                await message.channel.send(f"{message.author.mention}, words are not allowed!")
                warning_counter = get_warnings_and_inc(message.author.id, message.guild.id)
                if warning_counter >=3:
                    duration = datetime.timedelta(minutes=1)
                    await message.author.timeout(duration, reason="profanity")
                    await message.channel.send(f"{message.author.mention} has been timed out for 1 minute!")
    if "vylo" == message.content:
        await message.add_reaction("✅")
        await message.channel.send(f"{message.author.mention}, Vylo is online and functional.")
    
    await bot.process_commands(message) #mandatory to use to ensure the command functions are still processed

#EVENT HANDLERS FOR LOGGING
@bot.event
async def on_member_remove(member):
    await log_event("Member Left", f"{member.mention} left the server.", discord.Color.red())

@bot.event
async def on_message_delete(message):
    await log_event(
        "Message Deleted",
        f"**Author:** {message.author}\n**Channel:** {message.channel.mention}\n**Content:** {message.content}",
        discord.Color.red()
    )

@bot.event
async def on_message_edit(before, after):
    await log_event(
        "Message Edited",
        f"**Author:** {before.author}\n**Channel:** {before.channel.mention}\n**Before:** {before.content}\n**After:** {after.content}",
        discord.Color.yellow()
    )

@bot.event
async def on_member_update(before: discord.Member, after: discord.Member): #logs timeout and nickname changes
    changes = []

    if before.timed_out_until != after.timed_out_until:
        if after.timed_out_until:
            changes.append(f"Timed out until {after.timed_out_until}")
        else:
            changes.append("Timeout removed")

    if before.nick != after.nick:
        if before.nick:
            old_nick = before.nick
        else:
            old_nick = before.name

        if after.nick:
            new_nick = after.nick
        else:
            new_nick = after.name

        changes.append(f"Nickname changed from **{old_nick}** to **{new_nick}**")

    if changes:
        description = f"Member: {after.mention}\n" + "\n".join(changes)
        await log_event("Member Updated", description, discord.Color.blue())
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

@bot.command(
    name="unassign",
)
async def unassign(ctx, target_member: discord.Member, target_role: str):
    """removes a role from a specified member"""
    role = discord.utils.get(ctx.guild.roles, name=target_role)
    if role:
        await target_member.remove_roles(role)
        await ctx.send(f"{role} has been removed from {target_member.mention}")
    else:
        await ctx.send("No such role exists!")

@bot.command()
async def poll(ctx, *, msg):
    
    embed = discord.Embed(title=f"Poll generated by {ctx.author.name}\n", description=f"\n\n\n{msg}", timestamp = datetime.datetime.now())
    poll_message = await ctx.send(embed = embed)
    
    await poll_message.add_reaction("👍")
    await poll_message.add_reaction("👎")

@bot.command() #used to dynamically assign the log channel
@commands.has_permissions(administrator=True)
async def setlog(ctx, channel: discord.TextChannel):
    global LOG_CHANNEL_ID
    LOG_CHANNEL_ID = channel.id
    await ctx.send(f"Log channel set to {channel.mention}")

bot.run(token, log_handler=handler, log_level=logging.DEBUG) #EXECUTES THE BOT

