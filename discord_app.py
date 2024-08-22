import discord
from discord.ext import commands

# Create an instance of Intents with the necessary intents enabled
intents = discord.Intents.default()
intents.message_content = True  # Enables bot to read message content
intents.guilds = True  # Enables bot to manage guilds (servers)

# Create a bot instance with the specified intents
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command()
async def create_channel(ctx, channel_name: str):
    if ctx.guild is None:
        await ctx.send("This command can only be used in a server.")
        return

    guild = ctx.guild

    # Check if the bot has the manage channels permission
    if not guild.me.guild_permissions.manage_channels:
        await ctx.send("I don't have permission to create channels in this server.")
        return

    existing_channel = discord.utils.get(guild.channels, name=channel_name)

    if not existing_channel:
        print(f'Creating a new channel: {channel_name}')
        await guild.create_text_channel(channel_name)
        await ctx.send(f'Channel "{channel_name}" created successfully!')
    else:
        await ctx.send(f'Channel "{channel_name}" already exists.')

@bot.command()
async def send_message(ctx, channel_name: str, *, message: str):
    guild = ctx.guild
    channel = discord.utils.get(guild.text_channels, name=channel_name)
    if channel:
        await channel.send(message)
        await ctx.send(f'Message sent to {channel_name}: "{message}"')
    else:
        await ctx.send(f'Channel "{channel_name}" not found!')

# Run the bot with your token
bot.run('MTI3NjIwODYwOTQwNzAxMjk1NQ.GL50-m.3nLBbHr39A1xoLpRtJMAOwBM8Jz2oW8Dv_HCMU')