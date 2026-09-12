import asyncio
import base64
import json
import os
import platform
import random
import re
import subprocess
import sys
import time
import urllib.parse
import aiohttp
import requests
import speedtest  # Requires: pip install speedtest-cli
from pyDes import ECB, des, PAD_PKCS5
from telethon import Button, TelegramClient, events, functions
from telethon.errors import (
    PasswordHashInvalidError,
    PeerIdInvalidError,
    PhoneCodeInvalidError,
    SessionPasswordNeededError,
    UserIsBlockedError,
)
from telethon.tl.types import (
    ChatAdminRights,
    ChatBannedRights,
    DocumentAttributeAudio,
    ReactionEmoji,
    User,
)

# Optional Telegram voice-chat playback support
try:
    from pytgcalls import PyTgCalls

    HAS_PYTGCALLS = True
except ImportError:
    PyTgCalls = None
    HAS_PYTGCALLS = False
    print("⚠️ py-tgcalls not installed. !play/!vcl/!rvc/!endc/!cr/!vcopy will be unavailable. Install with: pip install -U py-tgcalls")

# Try importing psutil for detailed RAM & CPU health stats
try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# Try importing cryptg for faster Telegram file encryption/uploads
try:
    import cryptg

    HAS_CRYPTG = True
except ImportError:
    HAS_CRYPTG = False
    print(
        "⚠️ 'cryptg' not installed. Install with 'pip install cryptg' for maximum upload speed."
    )

CONFIG_FILE = "config.json"
SESSIONS_DIR = "sessions"
os.makedirs(SESSIONS_DIR, exist_ok=True)

# Global Set to Prevent Background Task Garbage Collection
RUNNING_TASKS = set()

# Uptime Tracker
START_TIME = time.time()

# Global System States
TARGET_USER = None
CUD_ACTIVE = False
ALL_MUTE_CHATS = set()
MUTED_USERS = set()
FLOOD_BYPASS = False

# Global Bot Execution Mode
SYSTEM_MODE = "eco"

ACTIVE_TARGET_LOOPS = {}
ACTIVE_REACTIONS = {}

HELP_MENU_CACHE = {}
ACTIVE_SONG_BOTS = {}
BOT_SEARCH_CACHE = {}

ACTIVE_USERBOTS = {}
PENDING_AUTH = {}
PENDING_BOT_LOADER = {}

# Interactive Setup State Tracker for Control Bot
SETUP_STATES = {}

# Voice-chat state: one persistent PyTgCalls engine per logged-in userbot
VOICE_CALLS = {}
VOICE_CALL_FILES = {}
ACTIVE_VOICE_LOOPS = {}  # Tracks active looping voice tasks per chat
ACTIVE_VCOPY_SESSIONS = {} # Tracks active VCOPY voice copy/relay sessions per chat

# Permanent Control Bot Configuration
CONTROL_BOT_TOKEN = "8982690377:AAEKlZgWy5L4m7swiOCHlpMKlfkDpq6crRQ"
CONTROL_CLIENT = None

# JioSaavn Base APIs
SEARCH_BASE_URL = "https://www.jiosaavn.com/api.php?__call=autocomplete.get&_format=json&_marker=0&cc=in&includeMetaTags=1&query="
SONG_DETAILS_BASE_URL = "https://www.jiosaavn.com/api.php?__call=song.getDetails&cc=in&_marker=0%3F_marker%3D0&_format=json&pids="

# Loop Command Message Templates
MSG_1 = """
<name> 𝗞𝗨𝗧𝗧𝗘 𝗖𝗨𝗗𝗡𝗔 𝗞𝗔𝗕 𝗦𝗧𝗔𝗥𝗧 𝗞𝗥𝗚𝗔?? 𝗥𝗡𝗗𝗬𝗖 🩷
<name> 𝗞𝗨𝗧𝗧𝗘 𝗖𝗨𝗗𝗡𝗔 𝗞𝗔𝗕 𝗦𝗧𝗔𝗥𝗧 𝗞𝗥𝗚𝗔?? 𝗥𝗡𝗗𝗬𝗖 🩷
<name> 𝗞𝗨𝗧𝗧𝗘 𝗖𝗨𝗗𝗡𝗔 𝗞𝗔𝗕 𝗦𝗧𝗔𝗥𝗧 𝗞𝗥𝗚𝗔?? 𝗥𝗡𝗗𝗬𝗖 🩷
<name> 𝗞𝗨𝗧𝗧𝗘 𝗖𝗨𝗗𝗡𝗔 𝗞𝗔𝗕 𝗦𝗧𝗔𝗥𝗧 𝗞𝗥𝗚𝗔?? 𝗥𝗡𝗗𝗬𝗖 🩷
<name> 𝗞𝗨𝗧𝗧𝗘 𝗖𝗨𝗗𝗡𝗔 𝗞𝗔𝗕 𝗦𝗧𝗔𝗥𝗧 𝗞𝗥𝗚𝗔?? 𝗥𝗡𝗗𝗬𝗖 🩷
<name> 𝗞𝗨𝗧𝗧𝗘 𝗖𝗨𝗗𝗡𝗔 𝗞𝗔𝗕 𝗦𝗧𝗔𝗥𝗧 𝗞𝗥𝗚𝗔?? 𝗥𝗡𝗗𝗬𝗖 🩷
<name> 𝗞𝗨𝗧𝗧𝗘 𝗖𝗨𝗗𝗡𝗔 𝗞𝗔𝗕 𝗦𝗧𝗔𝗥𝗧 𝗞𝗥𝗚𝗔?? 𝗥𝗡𝗗𝗬𝗖 🩷
<name> 𝗞𝗨𝗧𝗧𝗘 𝗖𝗨𝗗𝗡𝗔 𝗞𝗔𝗕 𝗦𝗧𝗔𝗥𝗧 𝗞𝗥𝗚𝗔?? 𝗥𝗡𝗗𝗬𝗖 🩷
<name> 𝗞𝗨𝗧𝗧𝗘 𝗖𝗨𝗗𝗡𝗔 𝗞𝗔𝗕 𝗦𝗧𝗔𝗥𝗧 𝗞𝗥𝗚𝗔?? 𝗥𝗡𝗗𝗬𝗖 🩷
<name> 𝗞𝗨𝗧𝗧𝗘 𝗖𝗨𝗗𝗡𝗔 𝗞𝗔𝗕 𝗦𝗧𝗔𝗥𝗧 𝗞𝗥𝗚𝗔?? 𝗥𝗡𝗗𝗬𝗖 🩷
<name> 𝗞𝗨𝗧𝗧𝗘 𝗖𝗨𝗗𝗡𝗔 𝗞𝗔𝗕 𝗦𝗧𝗔𝗥𝗧 𝗞𝗥𝗚𝗔?? 𝗥𝗡𝗗𝗬𝗖 🩷
<name> 𝗞𝗨𝗧𝗧𝗘 𝗖𝗨𝗗𝗡𝗔 𝗞𝗔𝗕 𝗦𝗧𝗔𝗥𝗧 𝗞𝗥𝗚𝗔?? 𝗥𝗡𝗗𝗬𝗖 🩷
<name> 𝗞𝗨𝗧𝗧𝗘 𝗖𝗨𝗗𝗡𝗔 𝗞𝗔𝗕 𝗦𝗧𝗔𝗥𝗧 𝗞𝗥𝗚𝗔?? 𝗥𝗡𝗗𝗬𝗖 🩷
<name> 𝗞𝗨𝗧𝗧𝗘 𝗖𝗨𝗗𝗡𝗔 𝗞𝗔𝗕 𝗦𝗧𝗔𝗥𝗧 𝗞𝗥𝗚𝗔?? 𝗥𝗡𝗗𝗬𝗖 🩷
<name> 𝗞𝗨𝗧𝗧𝗘 𝗖𝗨𝗗𝗡𝗔 𝗞𝗔𝗕 𝗦𝗧𝗔𝗥𝗧 𝗞𝗥𝗚𝗔?? 𝗥𝗡𝗗𝗬𝗖 🩷
<name> 𝗞𝗨𝗧𝗧𝗘 𝗖𝗨𝗗𝗡𝗔 𝗞𝗔𝗕 𝗦𝗧𝗔𝗥𝗧 𝗞𝗥𝗚𝗔?? 𝗥𝗡𝗗𝗬𝗖 🩷
<name> 𝗞𝗨𝗧𝗧𝗘 𝗖𝗨𝗗𝗡𝗔 𝗞𝗔𝗕 𝗦𝗧𝗔𝗥𝗧 𝗞𝗥𝗚𝗔?? 𝗥𝗡𝗗𝗬𝗖 🩷
<name> 𝗞𝗨𝗧𝗧𝗘 𝗖𝗨𝗗𝗡𝗔 𝗞𝗔𝗕 𝗦𝗧𝗔𝗥𝗧 𝗞𝗥𝗚𝗔?? 𝗥𝗡𝗗𝗬𝗖 🩷
""".strip()

MSG_2 = """
<name> 𝑻𝑬𝑹𝑰 𝑴𝑨𝑨 𝑲𝑰 𝑳𝑨𝑨𝑻𝑬𝒀  𝑻𝑶𝑫 𝑫𝑼 𝑴𝑪?? 💛
<name> 𝑻𝑬𝑹𝑰 𝑴𝑨𝑨 𝑲𝑰 𝑳𝑨𝑨𝑻𝑬𝒀  𝑻𝑶𝑫 𝑫𝑼 𝑴𝑪?? 💛
<name> 𝑻𝑬𝑹𝑰 𝑴𝑨𝑨 𝑲𝑰 𝑳𝑨𝑨𝑻𝑬𝒀  𝑻𝑶𝑫 𝑫𝑼 𝑴𝑪?? 💛
<name> 𝑻𝑬𝑹𝑰 𝑴𝑨𝑨 𝑲𝑰 𝑳𝑨𝑨𝑻𝑬𝒀  𝑻𝑶𝑫 𝑫𝑼 𝑴𝑪?? 💛
<name> 𝑻𝑬𝑹𝑰 𝑴𝑨𝑨 𝑲𝑰 𝑳𝑨𝑨𝑻𝑬𝒀  𝑻𝑶𝑫 𝑫𝑼 𝑴𝑪?? 💛
<name> 𝑻𝑬𝑹𝑰 𝑴𝑨𝑨 𝑲𝑰 𝑳𝑨𝑨𝑻𝑬𝒀  𝑻𝑶𝑫 𝑫𝑼 𝑴𝑪?? 💛
<name> 𝑻𝑬𝑹𝑰 𝑴𝑨𝑨 𝑲𝑰 𝑳𝑨𝑨𝑻𝑬𝒀  𝑻𝑶𝑫 𝑫𝑼 𝑴𝑪?? 💛
<name> 𝑻𝑬𝑹𝑰 𝑴𝑨𝑨 𝑲𝑰 𝑳𝑨𝑨𝑻𝑬𝒀  𝑻𝑶𝑫 𝑫𝑼 𝑴𝑪?? 💛
<name> 𝑻𝑬𝑹𝑰 𝑴𝑨𝑨 𝑲𝑰 𝑳𝑨𝑨𝑻𝑬𝒀  𝑻𝑶𝑫 𝑫𝑼 𝑴𝑪?? 💛
<name> 𝑻𝑬𝑹𝑰 𝑴𝑨𝑨 𝑲𝑰 𝑳𝑨𝑨𝑻𝑬𝒀  𝑻𝑶𝑫 𝑫𝑼 𝑴𝑪?? 💛
<name> 𝑻𝑬𝑹𝑰 𝑴𝑨𝑨 𝑲𝑰 𝑳𝑨𝑨𝑻𝑬𝒀  𝑻𝑶𝑫 𝑫𝑼 𝑴𝑪?? 💛
<name> 𝑻𝑬𝑹𝑰 𝑴𝑨𝑨 𝑲𝑰 𝑳𝑨𝑨𝑻𝑬𝒀  𝑻𝑶𝑫 𝑫𝑼 𝑴𝑪?? 💛
<name> 𝑻𝑬𝑹𝑰 𝑴𝑨𝑨 𝑲𝑰 𝑳𝑨𝑨𝑻𝑬𝒀  𝑻𝑶𝑫 𝑫𝑼 𝑴𝑪?? 💛
<name> 𝑻𝑬𝑹𝑰 𝑴𝑨𝑨 𝑲𝑰 𝑳𝑨𝑨𝑻𝑬𝒀  𝑻𝑶𝑫 𝑫𝑼 𝑴𝑪?? 💛
<name> 𝑻𝑬𝑹𝑰 𝑴𝑨𝑨 𝑲𝑰 𝑳𝑨𝑨𝑻𝑬𝒀  𝑻𝑶𝑫 𝑫𝑼 𝑴𝑪?? 💛
<name> 𝑻𝑬𝑹𝑰 𝑴𝑨𝑨 𝑲𝑰 𝑳𝑨𝑨𝑻𝑬𝒀  𝑻𝑶𝑫 𝑫𝑼 𝑴𝑪?? 💛
<name> 𝑻𝑬𝑹𝑰 𝑴𝑨𝑨 𝑲𝑰 𝑳𝑨𝑨𝑻𝑬𝒀  𝑻𝑶𝑫 𝑫𝑼 𝑴𝑪?? 💛
""".strip()

MSG_3 = """
ᴛᴡᴏ + ᴛᴡᴏ + ꜰᴏᴜʀ ? <name> ᴛᴇʀi ᴍᴀᴀ ᴋɪ ᴄʜᴜᴛ ᴍᴀᴀʀᴇʏ ᴄʜᴏʀ 💙
ᴛᴡᴏ + ᴛᴡᴏ + ꜰᴏᴜʀ ? <name> ᴛᴇʀi ᴍᴀᴀ ᴋɪ ᴄʜᴜᴛ ᴍᴀᴀʀᴇʏ ᴄʜᴏʀ 💙
ᴛᴡᴏ + ᴛᴡᴏ + ꜰᴏᴜʀ ? <name> ᴛᴇʀi ᴍᴀᴀ ᴋɪ ᴄʜᴜᴛ ᴍᴀᴀʀᴇʏ ᴄʜᴏʀ 💙
ᴛᴡᴏ + ᴛᴡᴏ + ꜰᴏᴜʀ ? <name> ᴛᴇʀi ᴍᴀᴀ ᴋɪ ᴄʜᴜᴛ ᴍᴀᴀʀᴇʏ ᴄʜᴏʀ 💙
ᴛᴡᴏ + ᴛᴡᴏ + ꜰᴏᴜʀ ? <name> ᴛᴇʀi ᴍᴀᴀ ᴋɪ ᴄʜᴜᴛ ᴍᴀᴀʀᴇʏ ᴄʜᴏʀ 💙
ᴛᴡᴏ + ᴛᴡᴏ + ꜰᴏᴜʀ ? <name> ᴛᴇʀi ᴍᴀᴀ ᴋɪ ᴄʜᴜᴛ ᴍᴀᴀʀᴇʏ ᴄʜᴏʀ 💙
ᴛᴡᴏ + ᴛᴡᴏ + ꜰᴏᴜʀ ? <name> ᴛᴇʀi ᴍᴀᴀ ᴋɪ ᴄʜᴜᴛ ᴍᴀᴀʀᴇʏ ᴄʜᴏʀ 💙
ᴛᴡᴏ + ᴛᴡᴏ + ꜰᴏᴜʀ ? <name> ᴛᴇʀi ᴍᴀᴀ ᴋɪ ᴄʜᴜᴛ ᴍᴀᴀʀᴇʏ ᴄʜᴏʀ 💙
ᴛᴡᴏ + ᴛᴡᴏ + ꜰᴏᴜʀ ? <name> ᴛᴇʀi ᴍᴀᴀ ᴋɪ ᴄʜᴜᴛ ᴍᴀᴀʀᴇʏ ᴄʜᴏʀ 💙
ᴛᴡᴏ + ᴛᴡᴏ + ꜰᴏᴜʀ ? <name> ᴛᴇʀi ᴍᴀᴀ ᴋɪ ᴄʜᴜᴛ ᴍᴀᴀʀᴇʏ ᴄʜᴏʀ 💙
ᴛᴡᴏ + ᴛᴡᴏ + ꜰᴏᴜʀ ? <name> ᴛᴇʀi ᴍᴀᴀ ᴋɪ ᴄʜᴜᴛ ᴍᴀᴀʀᴇʏ ᴄʜᴏʀ 💙
ᴛᴡᴏ + ᴛᴡᴏ + ꜰᴏᴜʀ ? <name> ᴛᴇʀi ᴍᴀᴀ ᴋɪ ᴄʜᴜᴛ ᴍᴀᴀʀᴇʏ ᴄʜᴏʀ 💙
""".strip()

LOOP_TEMPLATES = [MSG_1, MSG_2, MSG_3]

ASCII_ARTS = {
    "rose": """
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣤⢔⣒⠂⣀⣀⣤⣄⣀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⣴⣿⠋⢠⣟⡼⣷⠼⣆⣼⢇⣿⣄⠱⣄
⠀⠀⠀⠀⠀⠀⠀⠹⣿⡀⣆⠙⠢⠐⠉⠉⣴⣾⣽⢟⡰⠃
⠀⠀⠀⠀⠀⠀⠀⠀⠈⢿⣿⣦⠀⠤⢴⣿⠿⢋⣴⡏⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡙⠻⣿⣶⣦⣭⣉⠁⣿⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣷⠀⠈⠉⠉⠉⠉⠇⡟⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀I⠀⠀⣘⣦⣀⠀⠀⣀⡴⠊⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠈⠙⠛⠛⢻⣿⣿⣿⣿⠻⣧⡀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠫⣿⠉⠻⣇⠘⠓⠂⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠀⠀⠀⠀⠀⠀⠀⠀
⠀⢶⣾⣿⣿⣿⣿⣿⣶⣄⠀⠀⠀⣿⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠹⣿⣿⣿⣿⣿⣿⣿⣧⠀⢸⣿⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠈⠙Wait⠻⢿⣿⣿⠿⠛⣄⢸⡇⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⡁⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠁⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⡆⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⣷⠂⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿ Barb⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿ Barb⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠋⠀⠀⠀⠀⠀⠀⠀⠀
""",
    "cat": """
      /\_/\  
     ( o.o ) 
      > ^ <
""",
    "heart": """
  ████  ████  
 ██████████████ 
 ██████████████ 
    ████████████ 
     ██████████  
        ██████  
          ██  
""",
    "sword": """
         /| ________________
O|===|* >________________>
         \|
""",
    "skull": """
      ______
    .-'     `-.
   /         \\
  |           |
  |, .-. .-. ,|
  | )(__/ \\__)( |
  |/     /\\     \\|
  (_     ^^     _)
   \\__|IIIIII|__/
   | \\IIIIII/ |
   \\         /
    `--------`
""",
    "butterfly": """
      _   _
     (o)--(o)
    /.______.\\
    \\      /
   ./      \\.
  (  ▲   ▲  )
    \\      /
""",
    "dragon": """
        ,   ,
        (\____/)
        (_oo_)
        (O)
        __||__  \)
    []/______\[] /
    / \______/ \/
   /     /__\
  (\    /____\
""",
    "cool": """
  (⌐■_■)
""",
}

CUD_MESSAGES = [
    "TERI BAHEN K BOSDE ME AAAG😹❤️‍🔥😹❤️‍🔥😹❤️‍🔥😹❤️‍🔥😹",
    "🫩🫩🫩Cʜᴜᴘ रंडि k kalwe मदरचोद 🤢👋🏻",
    "Cʜᴀʟ ᵇᵃᵈᵃ ᵃʸᵃ ʳⁿᵈⁱ ᵏᵃ ᵇᵃᶜʰᵃ🐄🔥🐄🔥🐄🔥?",
    "🔺पिल्लै Tᴜᴊʜᴇ ᴍâRᴇɴɢᴇ ʏâʜɪ ᴅᴇʟʜɪ ᴍâYᴜR ᴠɪʜâR ᴍᴇ ᴊâB ᴍâRᴇɴɢᴇ ᴅᴇᴋʜ ʟེᱟ 🔥>💀",
    "𝐎ყᴇ 𝐁ᴇ𝐓ꪖ 𝐓ʀყ 𝐌ㄖ𝐌 𝐑ᴀRAN德y ❤️‍🔥❤️‍🩹🤍🖤💖💛💙💔fr?",
    "𝑻𝒆𝒓𝒊 𝑴𝒂𝒂 ᵗᵃᵏⁱ 𝑯𝒆̃̃ʜ𝒆hh𝒆💖💛💚💙💜 lol",
    "GᴀʟᴀT JᴀᴡᴀB Aʙ TᴇRɪ Mᴀ Kɪ CʜᴜᴅᴀI Hᴏɢᵢ 😁🙌🏻💝🔥😶",
    "NY NY KUCH NAHI SUNUNGA TERI TO MAA CUD GYI 🙌🏻😂🙌🏻😂🙌🏻😂🙌🏻😂🔥🔥ok...",
    "TERE GHAR KI AURTON KI BRA FAADH KE APNA KURTA SILWAUNGA RNDYK 🤍💚❤️🧡 🤔",
]

TARGET_TEMPLATES = [
    (
        "{name} CHUD TUNTUNE"
        "  𓍯😂𓍯𓍯😂𓍯𓍯😂𓍯𓍯😂𓍯𓍯😂𓍯𓍯😂𓍯𓍯😂𓍯𓍯😂𓍯𓍯😂𓍯𓍯😂𓍯"
    ),
    "{name} तेरी माँ की oral pills चूत😹💊😹💊😹💊😹💊",
    "{name} 𝑻𝒖𝒎🤢𝒔𝒂𝒃😱𝒓𝒂𝒏𝒅𝒊😎𝒌𝒆😍𝒃𝒂𝒄he😈𝒉𝒐🙀𝒏𝒂𝒉𝒊😝𝒎𝒂𝒏𝒐🥶𝒕𝒐🤡𝒂𝒑𝒏𝒊😂𝒎𝒂😭𝒄𝒉𝒖𝒅𝒂𝒐🤣",
    (
        "{name} Tery maa ke sir pe loda mardia na tappa khati khati gc se bahr"
        " gir jaygi"
    ),
    (
        "{name} तेरी माँ ke भोसड़े पे etne chappal maruga IPL जीत jayegi"
        " 😁🙌🏿🔥🔥🔥🔥❌❌"
    ),
    "Oye {name} Cʜᵃʟ ᵇᵃᵈᵃ ᵃʸᵃ ʳⁿᵈⁱ ᵏᵃ ᵇᵃᶜʰᵃ🐄🔥🐄🔥🐄🔥",
]

TEXT_TEMPLATES = [
    "💑 {name} 💑",
    "💖 {name} 💖",
    "💘 {name} 💘",
    "💟 {name} 💟",
    "💌 {name} 💌",
    "💞 {name} 💞",
]

ALL_COMMANDS = [
    "R <EMOJI>",
    "SR",
    "ECO",
    "RAGE",
    "LINK <PHONE>",
    "AUTH <CODE>",
    "BOTS",
    "DC <ID/USER>",
    "ST <TOKEN>",
    "LISTST",
    "REM <USER/IDX>",
    "CO <USER/ID/REPLY>",
    "DE <USER/ID/REPLY>",
    "COLIST / LISTCO",
    "ADD <USER/ID>",
    "PROMOTE <USER/ID>",
    "KICK <USER/ID>",
    "BMUTE <USER/ID>",
    "T <NAME>",
    "TS",
    "JOIN <LINK>",
    "ART <NAME>",
    "STATS",
    "LEAVE",
    "PURGE <COUNT/REPLY>",
    "CARBON <CODE/REPLY>",
    "1 <SONG>",
    "TTS <M/F> <TEXT>",
    "IMG <PROMPT>",
    "CHAT <QUERY>",
    "PING",
    "SPEEDTEST",
    "FIND <TARGET>",
    "ID",
    "DEL",
    "COPY",
    "RES",
    "BL <COUNT>",
    "B",
    "CLEARB",
    "IGNITE",
    "LOOP <NAME>",
    "SLOOP",
    "DLOOP <SECONDS>",
    "CR",
    "PLAY <REPLY AUDIO>",
    "VCL <REPLY AUDIO>",
    "RVC <REPLY AUDIO>",
    "VCOPY",
    "ENDC",
]


def load_config():
    default_structure = {
        "api_id": 25121973,
        "api_hash": "d9a7c8ce0b699cf8d93115cf6bf51cad",
        "phone": "",
        "owner_id": 0,
        "bot_password": "xns",
        "song_bots": [],
        "bot_users": {},
        "co_admins": [],
        "user_phones": [],
        "target_bots": [],
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                for key, default_val in default_structure.items():
                    if key not in data:
                        data[key] = default_val
                data["api_id"] = 25121973
                data["api_hash"] = "d9a7c8ce0b699cf8d93115cf6bf51cad"
                return data
        except Exception:
            pass

    save_config(default_structure)
    return default_structure


def save_config(data):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving config file: {e}")


def record_bot_user(bot_username, user_id):
    config = load_config()
    b_user = bot_username.lower()
    if b_user not in config["bot_users"]:
        config["bot_users"][b_user] = []

    if user_id not in config["bot_users"][b_user]:
        config["bot_users"][b_user].append(user_id)
        save_config(config)


def get_readable_time(seconds):
    days, remainder = divmod(int(seconds), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, secs = divmod(remainder, 60)

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")

    return " ".join(parts)


async def schedule_delete(*messages, delay=5):
    await asyncio.sleep(delay)
    for msg in messages:
        if msg:
            try:
                await msg.delete()
            except Exception:
                pass


def get_fast_session(ssl_verify=True):
    connector = aiohttp.TCPConnector(
        limit=100,
        ttl_dns_cache=300,
        enable_cleanup_closed=True,
        ssl=ssl_verify,
    )
    return aiohttp.ClientSession(connector=connector)


def perform_speedtest():
    st = speedtest.Speedtest()
    st.get_best_server()
    download_speed = st.download() / 1_000_000
    upload_speed = st.upload() / 1_000_000
    results = st.results.dict()
    return {
        "download": download_speed,
        "upload": upload_speed,
        "ping": results.get("ping", 0),
        "client_ip": results.get("client", {}).get("ip", "N/A"),
        "isp": results.get("client", {}).get("isp", "N/A"),
        "server_name": results.get("server", {}).get("name", "N/A"),
        "server_country": results.get("server", {}).get("country", "N/A"),
        "sponsor": results.get("server", {}).get("sponsor", "N/A"),
    }


def decrypt_media_url(encrypted_url):
    if not encrypted_url:
        return None
    try:
        key = b"38346591"
        des_cipher = des(key, ECB, b"\0\0\0\0\0\0\0\0", pad=None, padmode=PAD_PKCS5)
        enc_decoded = base64.b64decode(encrypted_url.strip())
        decrypted = des_cipher.decrypt(enc_decoded).decode("utf-8")
        url = decrypted.strip()
        return url.replace("http://", "https://") if url.startswith("http") else None
    except Exception as e:
        print(f"⚠️ Media decrypt error: {e}")
        return None


def generate_quality_urls(base_url, supports_320=True):
    if not base_url:
        return []
    urls = [{"quality": "Original", "url": base_url}]

    if supports_320:
        url_320 = base_url.replace("_96_p.mp4", "_320.mp4").replace("_96.mp4", "_320.mp4")
        if url_320 != base_url:
            urls.insert(0, {"quality": "320 kbps", "url": url_320})

    url_160 = base_url.replace("_96_p.mp4", "_160.mp4").replace("_96.mp4", "_160.mp4")
    if url_160 != base_url:
        urls.append({"quality": "160 kbps", "url": url_160})

    unique_urls = []
    seen = set()
    for item in urls:
        if item["url"] not in seen:
            seen.add(item["url"])
            unique_urls.append(item)
            
    return unique_urls


def fetch_jiosaavn_api(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        return response.json()
    except Exception:
        return {}


def search_songs(query):
    try:
        search_url = SEARCH_BASE_URL + requests.utils.quote(query)
        search_data = fetch_jiosaavn_api(search_url)

        if not search_data or not search_data.get("songs") or not search_data["songs"].get("data"):
            return []

        song_ids = ",".join([s["id"] for s in search_data["songs"]["data"][:5]])
        details_url = SONG_DETAILS_BASE_URL + song_ids
        details_data = fetch_jiosaavn_api(details_url)

        results = []
        for key in details_data:
            track = details_data[key]
            if isinstance(track, dict) and track.get("id"):
                media_url = track.get("media_url")
                encrypted_media_url = track.get("encrypted_media_url")
                supports_320 = str(track.get("320kbps", "")).lower() == "true"
                preview_url = track.get("media_preview_url")

                if not media_url and encrypted_media_url:
                    media_url = decrypt_media_url(encrypted_media_url)

                results.append({
                    "id": track["id"],
                    "name": track.get("song", "Unknown").replace("&quot;", '"'),
                    "artists": track.get("primary_artists", "Unknown").replace("&quot;", '"'),
                    "quality_urls": generate_quality_urls(media_url, supports_320),
                    "preview_url": preview_url
                })
        return results
    except Exception as e:
        print(f"❌ Search Error: {e}")
        return []


async def search_music_all(query):
    tracks = await asyncio.to_thread(search_songs, query)
    if tracks:
        return True, tracks
    return False, "No songs found."


async def download_file_ultra_fast(session, url, destination, headers=None):
    try:
        req_headers = headers or {"User-Agent": "Mozilla/5.0"}
        async with session.get(url, headers=req_headers, timeout=aiohttp.ClientTimeout(total=60)) as response:
            if response.status == 200 or response.status == 206:
                with open(destination, "wb") as f:
                    while True:
                        chunk = await response.content.read(1048576)
                        if not chunk:
                            break
                        f.write(chunk)
                return True
    except Exception as e:
        print(f"Fast Download Error: {e}")
    return False


async def start_song_bot_worker(api_id, api_hash, bot_token):
    session_name = os.path.join(SESSIONS_DIR, f"bot_session_{bot_token[:10]}")
    bot_client = TelegramClient(session_name, api_id, api_hash)

    try:
        await bot_client.start(bot_token=bot_token)
        bot_me = await bot_client.get_me()
        bot_username = bot_me.username.lower()

        @bot_client.on(events.NewMessage)
        async def song_bot_handler(event):
            text = event.raw_text.strip()
            user_id = event.sender_id

            if user_id:
                record_bot_user(bot_username, user_id)

            if text.startswith("/start"):
                welcome_text = (
                    f"⚡ **Welcome to @{bot_me.username}!**\n\n"
                    "Send me any song name or use `/s <song name>` for"
                    " ultra-fast downloads!\nClickable buttons offer instant"
                    " music processing."
                )
                await event.reply(welcome_text)
                return

            query = ""
            if (
                text.startswith("/s ")
                or text.startswith("/song ")
                or text.startswith("!s ")
            ):
                query = (
                    text.split(maxsplit=1)[1].strip()
                    if len(text.split()) > 1
                    else ""
                )
            elif not text.startswith("/"):
                query = text

            if not query:
                return

            status_msg = await event.reply(f"⚡ Searching: `{query}`...")

            success, results = await search_music_all(query)
            if not success:
                await status_msg.edit(f"❌ {results}")
                return

            top_results = results[:5]
            menu_text = f"🎵 **Select a song for `{query}`:**\n\n"
            buttons = []

            for idx, song in enumerate(top_results, 1):
                s_name = song.get("name", "Unknown Song")
                a_name = song.get("artists", "Artist")

                menu_text += f"**{idx}. {s_name}**\n   👤 {a_name}\n\n"
                buttons.append(
                    Button.inline(
                        f"{idx}️⃣ {s_name[:18]}", data=f"dl_{idx-1}"
                    )
                )

            button_grid = [
                buttons[i : i + 2] for i in range(0, len(buttons), 2)
            ]

            menu_msg = await status_msg.edit(menu_text, buttons=button_grid)
            BOT_SEARCH_CACHE[menu_msg.id] = top_results

        @bot_client.on(events.CallbackQuery)
        async def button_callback_handler(event):
            msg_id = event.message_id
            user_id = event.sender_id

            if user_id:
                record_bot_user(bot_username, user_id)

            if msg_id not in BOT_SEARCH_CACHE:
                await event.answer(
                    "❌ Search expired. Please search again.", alert=True
                )
                return

            data = event.data.decode("utf-8")
            if data.startswith("dl_"):
                idx = int(data.split("_")[1])
                song = BOT_SEARCH_CACHE[msg_id][idx]

                await event.answer("⚡ Downloading at max speed...")

                song_name = song.get("name", "Song")
                artist_names = song.get("artists", "Unknown Artist")
                quality_urls = song.get("quality_urls", [])

                song_url = quality_urls[0]["url"] if quality_urls else song.get("preview_url")

                if not song_url:
                    await event.edit(
                        f"❌ No downloadable link found for **{song_name}**."
                    )
                    return

                timestamp = int(time.time())
                audio_path = f"song_btn_{timestamp}.mp3"

                await event.edit(
                    f"🎵 **{song_name}**\n"
                    f"🎤 **Artist:** {artist_names}\n\n"
                    f"⚡ **Fast Downloading & Uploading...**",
                    buttons=None,
                )

                async with get_fast_session() as http_sess:
                    dl_success = await download_file_ultra_fast(
                        http_sess, song_url, audio_path
                    )

                if not dl_success or not os.path.exists(audio_path):
                    await event.edit("❌ Download failed from server.")
                    return

                audio_attr = DocumentAttributeAudio(
                    duration=0,
                    title=song_name,
                    performer=artist_names,
                )

                caption = (
                    f"🎵 **{song_name}**\n🎤 **Artist:** {artist_names}\n⚡"
                    f" **Downloaded via:** @{bot_me.username}"
                )

                await bot_client.send_file(
                    event.chat_id,
                    audio_path,
                    caption=caption,
                    attributes=[audio_attr],
                    reply_to=event.message_id,
                )

                try:
                    await bot_client.delete_messages(
                        event.chat_id, [msg_id]
                    )
                except Exception:
                    pass

                if msg_id in BOT_SEARCH_CACHE:
                    del BOT_SEARCH_CACHE[msg_id]

                if audio_path and os.path.exists(audio_path):
                    os.remove(audio_path)

        task = asyncio.create_task(bot_client.run_until_disconnected())
        RUNNING_TASKS.add(task)
        task.add_done_callback(RUNNING_TASKS.discard)

        ACTIVE_SONG_BOTS[bot_username] = {
            "client": bot_client,
            "task": task,
            "token": bot_token,
            "bot_id": bot_me.id,
        }
        return True, bot_username
    except Exception as e:
        return False, str(e)


def attach_userbot_handlers(client, phone_number):
    config = load_config()
    primary_phone = config.get("phone")

    @client.on(events.NewMessage)
    async def global_handler(event):
        global TARGET_USER, CUD_ACTIVE, ALL_MUTE_CHATS, MUTED_USERS, FLOOD_BYPASS, HELP_MENU_CACHE
        global ACTIVE_TARGET_LOOPS, ACTIVE_REACTIONS, PENDING_AUTH, PENDING_BOT_LOADER, ACTIVE_USERBOTS, SYSTEM_MODE

        owner_id = config.get("owner_id")
        co_admins = config.get("co_admins", [])

        is_authorized = (
            event.sender_id == owner_id or event.sender_id in co_admins
        )
        is_primary_bot = phone_number == primary_phone

        if event.chat_id in ACTIVE_REACTIONS and is_authorized:
            emoji = ACTIVE_REACTIONS[event.chat_id]
            try:
                await event.react(emoji)
            except Exception:
                try:
                    await client(
                        functions.messages.SendReactionRequest(
                            peer=event.chat_id,
                            msg_id=event.id,
                            reaction=[ReactionEmoji(emoticon=emoji)],
                        )
                    )
                except Exception:
                    pass

        if SYSTEM_MODE == "eco" and not is_primary_bot:
            return

        if is_primary_bot and event.chat_id in PENDING_AUTH and is_authorized:
            raw_input = event.raw_text.strip()
            text_lower = raw_input.lower()

            if text_lower.startswith("!auth "):
                auth_info = PENDING_AUTH[event.chat_id]
                code_arg = raw_input[6:].strip()
                status_msg_id = auth_info["status_msg_id"]
                target_phone = auth_info["phone"]
                temp_client = auth_info["client"]
                state = auth_info["state"]

                if state == "WAITING_OTP":
                    otp_code = re.sub(r"\D", "", code_arg)
                    if not otp_code:
                        res = await event.reply(
                            "⚠️ **Usage:** `!auth <otp_code>`"
                        )
                        task = asyncio.create_task(
                            schedule_delete(event, res, delay=5)
                        )
                        RUNNING_TASKS.add(task)
                        task.add_done_callback(RUNNING_TASKS.discard)
                        return

                    await client.edit_message(
                        event.chat_id,
                        status_msg_id,
                        f"🔑 **Verifying OTP Code:** `{otp_code}`...",
                    )

                    try:
                        await temp_client.sign_in(
                            target_phone,
                            otp_code,
                            phone_code_hash=auth_info["phone_code_hash"],
                        )
                        await temp_client.disconnect()
                        del PENDING_AUTH[event.chat_id]

                        cfg = load_config()
                        if target_phone not in cfg["user_phones"]:
                            cfg["user_phones"].append(target_phone)
                            save_config(cfg)

                        task = asyncio.create_task(
                            start_userbot_instance(
                                cfg["api_id"], cfg["api_hash"], target_phone
                            )
                        )
                        RUNNING_TASKS.add(task)
                        task.add_done_callback(RUNNING_TASKS.discard)

                        await client.edit_message(
                            event.chat_id,
                            status_msg_id,
                            "✅ **Success!** Linked new userbot.\nUserbot is now"
                            " online & running!",
                        )
                        task2 = asyncio.create_task(
                            schedule_delete(event, delay=1)
                        )
                        RUNNING_TASKS.add(task2)
                        task2.add_done_callback(RUNNING_TASKS.discard)
                        return

                    except SessionPasswordNeededError:
                        auth_info["state"] = "WAITING_2FA"
                        await client.edit_message(
                            event.chat_id,
                            status_msg_id,
                            "🔐 **2FA Password Required!**\n\nPlease enter"
                            " your password using:\n`!auth <2fa_password>`",
                        )
                        task = asyncio.create_task(
                            schedule_delete(event, delay=1)
                        )
                        RUNNING_TASKS.add(task)
                        task.add_done_callback(RUNNING_TASKS.discard)
                        return

                    except PhoneCodeInvalidError:
                        await client.edit_message(
                            event.chat_id,
                            status_msg_id,
                            "❌ **Invalid OTP Code!** Please try linking"
                            " again using `!link <phone>`.",
                        )
                        await temp_client.disconnect()
                        del PENDING_AUTH[event.chat_id]
                        task = asyncio.create_task(
                            schedule_delete(event, delay=1)
                        )
                        RUNNING_TASKS.add(task)
                        task.add_done_callback(RUNNING_TASKS.discard)
                        return

                    except Exception as e:
                        await client.edit_message(
                            event.chat_id,
                            status_msg_id,
                            f"❌ **OTP Sign-In Error:** `{str(e)}`",
                        )
                        await temp_client.disconnect()
                        del PENDING_AUTH[event.chat_id]
                        task = asyncio.create_task(
                            schedule_delete(event, delay=1)
                        )
                        RUNNING_TASKS.add(task)
                        task.add_done_callback(RUNNING_TASKS.discard)
                        return

                elif state == "WAITING_2FA":
                    password = code_arg
                    if not password:
                        res = await event.reply(
                            "⚠️ **Usage:** `!auth <2fa_password>`"
                        )
                        task = asyncio.create_task(
                            schedule_delete(event, res, delay=5)
                        )
                        RUNNING_TASKS.add(task)
                        task.add_done_callback(RUNNING_TASKS.discard)
                        return

                    await client.edit_message(
                        event.chat_id,
                        status_msg_id,
                        "🔐 **Verifying 2FA Password...**",
                    )

                    try:
                        await temp_client.sign_in(password=password)
                        await temp_client.disconnect()
                        del PENDING_AUTH[event.chat_id]

                        cfg = load_config()
                        if target_phone not in cfg["user_phones"]:
                            cfg["user_phones"].append(target_phone)
                            save_config(cfg)

                        task = asyncio.create_task(
                            start_userbot_instance(
                                cfg["api_id"], cfg["api_hash"], target_phone
                            )
                        )
                        RUNNING_TASKS.add(task)
                        task.add_done_callback(RUNNING_TASKS.discard)

                        await client.edit_message(
                            event.chat_id,
                            status_msg_id,
                            "✅ **Success!** Linked new userbot.\nUserbot is now"
                            " online & running!",
                        )
                        task2 = asyncio.create_task(
                            schedule_delete(event, delay=1)
                        )
                        RUNNING_TASKS.add(task2)
                        task2.add_done_callback(RUNNING_TASKS.discard)
                        return

                    except PasswordHashInvalidError:
                        await client.edit_message(
                            event.chat_id,
                            status_msg_id,
                            "❌ **Incorrect 2FA Password!** Linking failed. Try"
                            " again with `!link <phone>`.",
                        )
                        await temp_client.disconnect()
                        del PENDING_AUTH[event.chat_id]
                        task = asyncio.create_task(
                            schedule_delete(event, delay=1)
                        )
                        RUNNING_TASKS.add(task)
                        task.add_done_callback(RUNNING_TASKS.discard)
                        return

                    except Exception as e:
                        await client.edit_message(
                            event.chat_id,
                            status_msg_id,
                            f"❌ **2FA Sign-In Error:** `{str(e)}`",
                        )
                        await temp_client.disconnect()
                        del PENDING_AUTH[event.chat_id]
                        task = asyncio.create_task(
                            schedule_delete(event, delay=1)
                        )
                        RUNNING_TASKS.add(task)
                        task.add_done_callback(RUNNING_TASKS.discard)
                        return

        if (
            is_primary_bot
            and event.chat_id in PENDING_BOT_LOADER
            and is_authorized
        ):
            raw_inp = event.raw_text.strip()
            if not raw_inp.startswith("!"):
                bot_user = raw_inp if raw_inp.startswith("@") else f"@{raw_inp}"
                loader_data = PENDING_BOT_LOADER[event.chat_id]
                loader_data["collected"].append(bot_user)

                curr_len = len(loader_data["collected"])
                tot_len = loader_data["total"]

                if curr_len < tot_len:
                    res = await event.reply(
                        f"✅ Saved bot `{bot_user}`"
                        f" ({curr_len}/{tot_len}).\nSend Bot"
                        f" **#{curr_len + 1}** username:"
                    )
                else:
                    cfg = load_config()
                    if "target_bots" not in cfg:
                        cfg["target_bots"] = []

                    for b in loader_data["collected"]:
                        if b not in cfg["target_bots"]:
                            cfg["target_bots"].append(b)

                    save_config(cfg)
                    del PENDING_BOT_LOADER[event.chat_id]
                    res = await event.reply(
                        f"🎉 **Finished!** Successfully saved `{tot_len}`"
                        " target bot(s) to configuration!\nType `!b` to view"
                        " all saved bots or `!ignite` to auto-add & promote"
                        " them."
                    )

                task = asyncio.create_task(
                    schedule_delete(event, res, delay=8)
                )
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

        if FLOOD_BYPASS:
            client.flood_sleep_threshold = 0
        else:
            client.flood_sleep_threshold = 60

        if (
            event.chat_id in ALL_MUTE_CHATS
            and event.sender_id != owner_id
            and event.sender_id not in co_admins
        ):
            await asyncio.sleep(0.1)
            await event.delete()
            return

        if (
            event.sender_id in MUTED_USERS
            and event.sender_id != owner_id
            and event.sender_id not in co_admins
        ):
            await asyncio.sleep(0.1)
            await event.delete()
            return

        if CUD_ACTIVE and event.sender_id == TARGET_USER:
            await event.reply(random.choice(CUD_MESSAGES))
            return

        me = await client.get_me()
        if (
            event.chat_id in ACTIVE_TARGET_LOOPS
            and ACTIVE_TARGET_LOOPS[event.chat_id].get("active")
            and event.sender_id != me.id
        ):
            target_name = ACTIVE_TARGET_LOOPS[event.chat_id].get(
                "name", "User"
            )
            template = random.choice(TEXT_TEMPLATES)
            msg_text = template.format(name=target_name)
            try:
                await event.reply(msg_text)
            except Exception:
                pass

        if not is_authorized:
            return

        text = event.raw_text.lower()
        reply = await event.get_reply_message()

        # VOICE CHAT COMMANDS & VCOPY
        if text == "!play" or text.startswith("!play "):
            await play_replied_audio(event, phone_number, reply)
            return

        elif text == "!vcl" or text.startswith("!vcl "):
            await play_replied_audio(event, phone_number, reply)
            return

        elif text == "!rvc" or text.startswith("!rvc "):
            await play_loop_all_userbots(event, reply)
            return

        elif text == "!vcopy" or text.startswith("!vcopy "):
            await start_vcopy_feature(event, client, phone_number)
            return

        elif text == "!cr":
            await join_voice_call_all(event)
            return

        elif text == "!endc" or text.startswith("!endc "):
            await end_voice_call_all(event)
            return

        # Commands Processing
        if text.startswith("!r ") or text == "!r":
            args = event.raw_text.split(maxsplit=1)
            emoji = args[1].strip() if len(args) > 1 else "❤️"

            ACTIVE_REACTIONS[event.chat_id] = emoji

            target_msg = reply if reply else event
            success_count = 0
            error_msg = ""

            for ph, bot_cli in list(ACTIVE_USERBOTS.items()):
                try:
                    await target_msg.react(emoji)
                    success_count += 1
                except Exception as e:
                    error_msg = str(e)
                    try:
                        await bot_cli(
                            functions.messages.SendReactionRequest(
                                peer=event.chat_id,
                                msg_id=target_msg.id,
                                reaction=[ReactionEmoji(emoticon=emoji)],
                            )
                        )
                        success_count += 1
                    except Exception as err:
                        error_msg = str(err)
                        print(f"Reaction failed for userbot {ph}: {err}")

            if success_count > 0:
                res = await event.reply(
                    f"🔥 **Auto-reaction enabled with `{emoji}`!**\nAll userbots reacted successfully."
                )
            else:
                hint = ""
                if "only emoji are allowed" in error_msg.lower() or "invalid reaction" in error_msg.lower():
                    hint = "\n*(Note: Custom or premium emojis require a Telegram Premium account on the userbot.)*"
                
                res = await event.reply(
                    f"⚠️ **Reaction set to `{emoji}`, but failed to send.**{hint}\n`{error_msg}`"
                )

            task = asyncio.create_task(schedule_delete(event, res, delay=8))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text == "!sr" or text.startswith("!sr "):
            if event.chat_id in ACTIVE_REACTIONS:
                del ACTIVE_REACTIONS[event.chat_id]
                res = await event.reply(
                    "🛑 **Auto-reaction disabled for this chat.**"
                )
            else:
                res = await event.reply(
                    "ℹ️ **Auto-reaction is not currently active in this chat.**"
                )

            task = asyncio.create_task(schedule_delete(event, res, delay=5))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text == "!eco" or text.startswith("!eco "):
            if not is_primary_bot:
                return

            SYSTEM_MODE = "eco"
            res = await event.reply(
                "🌱 **ECO Mode Activated!**\nOnly the primary userbot will"
                " perform tasks and reply to commands."
            )
            task = asyncio.create_task(schedule_delete(event, res, delay=5))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text == "!rage" or text.startswith("!rage "):
            if not is_primary_bot:
                return

            SYSTEM_MODE = "rage"
            res = await event.reply(
                f"🔥 **RAGE Mode Activated!**\nAll `{len(ACTIVE_USERBOTS)}`"
                " connected userbots are now actively executing tasks."
            )
            task = asyncio.create_task(schedule_delete(event, res, delay=5))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text.startswith("!link "):
            if not is_primary_bot:
                return

            raw_phone = event.raw_text[6:].strip()
            phone = re.sub(r"[^\d+]", "", raw_phone)

            if not phone:
                res = await event.reply(
                    "⚠️ **Usage:** `!link <phone_number_with_country_code>`"
                )
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            status_msg = await event.reply(
                "📡 **Initiating OTP request...**"
            )

            phone_clean = re.sub(r"\D", "", phone)
            temp_session = os.path.join(SESSIONS_DIR, f"userbot_{phone_clean}")
            temp_client = TelegramClient(
                temp_session, config["api_id"], config["api_hash"]
            )

            try:
                await temp_client.connect()
                send_code_res = await temp_client.send_code_request(phone)

                PENDING_AUTH[event.chat_id] = {
                    "phone": phone,
                    "phone_code_hash": send_code_res.phone_code_hash,
                    "client": temp_client,
                    "status_msg_id": status_msg.id,
                    "state": "WAITING_OTP",
                }

                await status_msg.edit(
                    f"📩 **OTP sent successfully!**\n\n👉 **Send the OTP using"
                    " the command:**\n`!auth <otp_code>`"
                )

            except Exception as e:
                await status_msg.edit(
                    f"❌ **Failed to send OTP:** `{str(e)}`"
                )
                await temp_client.disconnect()
                task = asyncio.create_task(
                    schedule_delete(event, status_msg, delay=8)
                )
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

        elif text.startswith("!bl"):
            args = event.raw_text.split(maxsplit=1)
            if len(args) < 2 or not args[1].strip().isdigit():
                res = await event.reply(
                    "⚠️ **Usage:** `!bl <number_of_bots>`\n*Example:* `!bl 3`"
                )
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            count = int(args[1].strip())
            if count <= 0:
                res = await event.reply(
                    "❌ **Please enter a number greater than 0.**"
                )
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            PENDING_BOT_LOADER[event.chat_id] = {
                "total": count,
                "collected": [],
            }
            res = await event.reply(
                f"🤖 **Bot Loader Started!**\nYou requested to save `{count}`"
                " bot(s).\n\nSend Bot **#1** username (e.g. `@my_bot`):"
            )
            task = asyncio.create_task(schedule_delete(event, res, delay=10))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text == "!b" or text.startswith("!b "):
            cfg = load_config()
            saved_bots = cfg.get("target_bots", [])
            if not saved_bots:
                res = await event.reply(
                    "ℹ️ **No target bots saved in config yet.** Use `!bl"
                    " <count>` to add bots."
                )
            else:
                bot_list_str = "🤖 **SAVED TARGET BOTS LIST:**\n\n"
                for idx, b_name in enumerate(saved_bots, 1):
                    bot_list_str += f"**{idx}.** {b_name}\n"
                bot_list_str += (
                    f"\n💡 **Total Saved:** `{len(saved_bots)}` bots\nType"
                    " `!ignite` to automatically add and promote all bots in"
                    " this group!"
                )
                res = await event.reply(bot_list_str)

            task = asyncio.create_task(schedule_delete(event, res, delay=15))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text == "!clearb" or text.startswith("!clearb "):
            cfg = load_config()
            cfg["target_bots"] = []
            save_config(cfg)
            res = await event.reply(
                "🗑️ **Cleared all saved target bots from configuration!**"
            )
            task = asyncio.create_task(schedule_delete(event, res, delay=5))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text == "!ignite" or text.startswith("!ignite "):
            if event.is_private:
                res = await event.reply(
                    "❌ **This command can only be used in groups!**"
                )
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            cfg = load_config()
            target_bots = cfg.get("target_bots", [])

            if not target_bots:
                res = await event.reply(
                    "⚠️ **No target bots saved in config!** First add bots using"
                    " `!bl <count>`."
                )
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            status_msg = await event.reply(
                "🚀 **Igniting Bot Auto-Inserter & Admin Promoter...**\nTarget"
                f" Bots: `{len(target_bots)}`"
            )

            added_count = 0
            promoted_count = 0
            failed_count = 0

            admin_rights = ChatAdminRights(
                change_info=True,
                delete_messages=True,
                ban_users=True,
                invite_users=True,
                pin_messages=True,
                add_admins=False,
                manage_call=True,
            )

            for b_user in target_bots:
                try:
                    bot_entity = await client.get_entity(b_user)

                    try:
                        await client(
                            functions.channels.InviteToChannelRequest(
                                event.chat_id, [bot_entity]
                            )
                        )
                        added_count += 1
                        await asyncio.sleep(1.5)
                    except Exception as add_err:
                        print(f"Invite note for {b_user}: {add_err}")

                    await client(
                        functions.channels.EditAdminRequest(
                            channel=event.chat_id,
                            user_id=bot_entity.id,
                            admin_rights=admin_rights,
                            rank="Bot Admin",
                        )
                    )
                    promoted_count += 1
                    await asyncio.sleep(1.5)

                except Exception as e:
                    print(f"Ignite Error for bot {b_user}: {e}")
                    failed_count += 1

            result_str = (
                "🔥 **IGNITE PROCESS FINISHED!**\n\n"
                f"📥 **Bots Added:** `{added_count}`\n"
                f"👑 **Bots Promoted to Admin:** `{promoted_count}`\n"
                f"❌ **Failed:** `{failed_count}`"
            )
            await status_msg.edit(result_str)
            task = asyncio.create_task(
                schedule_delete(event, status_msg, delay=15)
            )
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text == "!bots" or text.startswith("!bots "):
            if not is_primary_bot:
                return

            if not ACTIVE_USERBOTS:
                res = await event.reply(
                    "ℹ️ **No active userbots connected.**"
                )
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            msg = await event.reply(
                "📋 **Fetching all active connected userbots...**"
            )
            bots_text = (
                "🤖 **CONNECTED USERBOTS LIST** (Mode:"
                f" `{SYSTEM_MODE.upper()}`):\n\n"
            )

            idx = 1
            for ph, bot_cli in list(ACTIVE_USERBOTS.items()):
                try:
                    bot_me = await bot_cli.get_me()
                    b_name = (
                        f"{bot_me.first_name or ''} {bot_me.last_name or ''}".strip()
                        or "Userbot"
                    )
                    b_user = (
                        f"@{bot_me.username}"
                        if bot_me.username
                        else "No Username"
                    )
                    is_main = " 👑 *(Primary)*" if ph == primary_phone else ""

                    bots_text += (
                        f"**{idx}. {b_name}**{is_main}\n"
                        f"   ├ 🆔 Chat/User ID: `{bot_me.id}`\n"
                        f"   └ 🏷️ Username: {b_user}\n\n"
                    )
                    idx += 1
                except Exception:
                    bots_text += (
                        f"**{idx}. Userbot** *(Error fetching details)*\n\n"
                    )
                    idx += 1

            bots_text += (
                "💡 **To disconnect a userbot, use:**\n`!dc <Chat ID or"
                " Username>`"
            )
            await msg.edit(bots_text)
            task = asyncio.create_task(schedule_delete(event, msg, delay=15))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text.startswith("!dc "):
            if not is_primary_bot:
                return

            query = event.raw_text[4:].strip().lower().replace("@", "")
            if not query:
                res = await event.reply(
                    "⚠️ **Usage:** `!dc <chat_id or username>`"
                )
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            msg = await event.reply(
                f"⏳ **Searching userbot account to remove:** `{query}`..."
            )
            found_phone = None
            found_id = None
            found_username = None

            for ph, bot_cli in list(ACTIVE_USERBOTS.items()):
                try:
                    bot_me = await bot_cli.get_me()
                    curr_username = (bot_me.username or "").lower()
                    curr_id = str(bot_me.id)

                    if query == curr_id or query == curr_username:
                        found_phone = ph
                        found_id = bot_me.id
                        found_username = bot_me.username
                        break
                except Exception:
                    pass

            if not found_phone:
                await msg.edit(
                    f"❌ **Userbot account `{query}` not found!** Check active"
                    " list with `!bots`."
                )
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            if found_phone == primary_phone:
                await msg.edit(
                    "❌ **Cannot remove the main primary userbot account!**"
                )
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            try:
                call = VOICE_CALLS.pop(found_phone, None)
                if call:
                    try:
                        pass
                    except Exception:
                        pass

                target_cli = ACTIVE_USERBOTS[found_phone]
                await target_cli.disconnect()
                del ACTIVE_USERBOTS[found_phone]

                cfg = load_config()
                if found_phone in cfg.get("user_phones", []):
                    cfg["user_phones"].remove(found_phone)
                    save_config(cfg)

                phone_clean = re.sub(r"\D", "", found_phone)
                session_file = os.path.join(
                    SESSIONS_DIR, f"userbot_{phone_clean}.session"
                )
                if os.path.exists(session_file):
                    try:
                        os.remove(session_file)
                    except Exception:
                        pass

                u_str = f" (@{found_username})" if found_username else ""
                await msg.edit(
                    "✅ **Successfully disconnected and removed userbot!**\n🆔"
                    f" **ID:** `{found_id}`{u_str}"
                )
            except Exception as e:
                await msg.edit(
                    f"❌ **Error while removing userbot:** `{str(e)}`"
                )

            task = asyncio.create_task(schedule_delete(event, msg, delay=8))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text.startswith("!art"):
            args = event.raw_text.split(maxsplit=1)
            art_key = args[1].strip().lower() if len(args) > 1 else ""

            if art_key in ASCII_ARTS:
                chosen_art = ASCII_ARTS[art_key]
            else:
                art_key, chosen_art = random.choice(list(ASCII_ARTS.items()))

            await event.respond(f"```\n{chosen_art.strip()}\n```")
            task = asyncio.create_task(schedule_delete(event, delay=1))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text == "!stats" or text.startswith("!stats "):
            status_msg = await event.reply(
                "📊 **Gathering system health & bot stats...**"
            )

            uptime_str = get_readable_time(time.time() - START_TIME)
            py_ver = platform.python_version()
            sys_os = f"{platform.system()} {platform.release()}"

            bot_users_dict = config.get("bot_users", {})
            total_served = sum(
                len(u_list) for u_list in bot_users_dict.values()
            )

            stats_text = (
                "╔══『 📊 **BOT HEALTH ** 』══╗\n\n"
                f"⏱️ **Uptime:** `{uptime_str}`\n"
                f"🚀 **Bot Status:** `Online & Ready`\n"
                f"⚡ **Active Mode:** `{SYSTEM_MODE.upper()}`\n"
                f"📱 **Active Userbots:** `{len(ACTIVE_USERBOTS)}` logged in\n"
                f"🐍 **Python:** `v{py_ver}`\n"
                f"💻 **OS:** `{sys_os}`\n\n"
                f"👑 **Co-Admins:** `{len(co_admins)}` active\n"
                f"🤖 **Song Bots:** `{len(ACTIVE_SONG_BOTS)}` active\n"
                f"👥 **Total Users Served:** `{total_served}`\n"
            )

            if HAS_PSUTIL:
                cpu_usage = psutil.cpu_percent(interval=0.5)
                ram = psutil.virtual_memory()
                ram_used = ram.used / (1024**3)
                ram_total = ram.total / (1024**3)
                stats_text += (
                    f"\n🧠 **CPU Usage:** `{cpu_usage}%`\n"
                    f"💾 **RAM:** `{ram_used:.2f} GB / {ram_total:.2f} GB`"
                    f" ({ram.percent}%)\n"
                )

            stats_text += "\n╚═════『 𝗫𝗡𝗦 V.03 』══════╝"
            await status_msg.edit(stats_text)
            task = asyncio.create_task(
                schedule_delete(event, status_msg, delay=15)
            )
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text.startswith("!carbon"):
            code_text = ""
            args = event.raw_text.split(maxsplit=1)

            if len(args) > 1:
                code_text = args[1].strip()
            elif reply and reply.raw_text:
                code_text = reply.raw_text.strip()

            if not code_text:
                res = await event.reply(
                    "⚠️ **Usage:** Reply to code/text with `!carbon` OR type"
                    " `!carbon <code>`"
                )
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            status_msg = await event.reply(
                "🎨 **Cooking Carbon snippet image...**"
            )
            success, result = await make_carbon_image(code_text)

            if success and os.path.exists(result):
                try:
                    await client.send_file(
                        event.chat_id,
                        result,
                        caption="🎨 **Carbon Snippet Generated!**",
                        reply_to=reply.id if reply else event.id,
                    )
                    os.remove(result)
                    task = asyncio.create_task(
                        schedule_delete(status_msg, delay=1)
                    )
                    RUNNING_TASKS.add(task)
                    task.add_done_callback(RUNNING_TASKS.discard)
                except Exception as e:
                    await status_msg.edit(
                        f"❌ **Failed to send image:** `{str(e)[:100]}`"
                    )
                    task = asyncio.create_task(
                        schedule_delete(event, status_msg, delay=5)
                    )
                    RUNNING_TASKS.add(task)
                    task.add_done_callback(RUNNING_TASKS.discard)
            else:
                await status_msg.edit(
                    f"❌ **Carbon Generation Failed:** `{result}`"
                )
                task = asyncio.create_task(
                    schedule_delete(event, status_msg, delay=5)
                )
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text.startswith("!t "):
            target_name = event.raw_text[3:].strip()

            if target_name.lower() in ["stop", "s"] or text == "!ts":
                if (
                    event.chat_id not in ACTIVE_TARGET_LOOPS
                    or not ACTIVE_TARGET_LOOPS[event.chat_id].get("active")
                ):
                    res = await event.reply(
                        "ℹ️ **No active tmode loop running in this chat.**"
                    )
                else:
                    ACTIVE_TARGET_LOOPS[event.chat_id]["active"] = False
                    res = await event.reply(
                        "🛑 **Tmode loop stopped for this chat!**"
                    )

                task = asyncio.create_task(
                    schedule_delete(event, res, delay=5)
                )
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            if not target_name:
                res = await event.reply(
                    "⚠️ **Usage:** `!t <text>` or `!t stop` / `!ts`"
                )
                task = asyncio.create_task(
                    schedule_delete(event, res, delay=5)
                )
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            if (
                event.chat_id in ACTIVE_TARGET_LOOPS
                and ACTIVE_TARGET_LOOPS[event.chat_id].get("active")
            ):
                ACTIVE_TARGET_LOOPS[event.chat_id]["active"] = False

            task = asyncio.create_task(
                target_message_loop(client, event.chat_id, target_name)
            )
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)

            ACTIVE_TARGET_LOOPS[event.chat_id] = {
                "active": True,
                "name": target_name,
                "task": task,
            }

            res = await event.reply(
                "🔥 **Tmode loop started in this chat for:**"
                f" `{target_name}`"
            )
            task2 = asyncio.create_task(schedule_delete(event, res, delay=5))
            RUNNING_TASKS.add(task2)
            task2.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text == "!ts":
            if (
                event.chat_id not in ACTIVE_TARGET_LOOPS
                or not ACTIVE_TARGET_LOOPS[event.chat_id].get("active")
            ):
                res = await event.reply(
                    "ℹ️ **No active tmode loop running in this chat.**"
                )
            else:
                ACTIVE_TARGET_LOOPS[event.chat_id]["active"] = False
                res = await event.reply(
                    "🛑 **T loop stopped for this chat!**"
                )

            task = asyncio.create_task(schedule_delete(event, res, delay=5))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text.startswith("!loop "):
            loop_name = event.raw_text[6:].strip()
            if not loop_name:
                res = await event.reply("⚠️ **Usage:** `!loop <name>`")
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            chat_id = event.chat_id
            if chat_id not in ACTIVE_TARGET_LOOPS:
                ACTIVE_TARGET_LOOPS[chat_id] = {}

            ACTIVE_TARGET_LOOPS[chat_id]["loop_active"] = False
            await asyncio.sleep(0.3)

            current_delay = ACTIVE_TARGET_LOOPS[chat_id].get("loop_delay", 1.5)
            ACTIVE_TARGET_LOOPS[chat_id]["loop_active"] = True
            ACTIVE_TARGET_LOOPS[chat_id]["loop_name"] = loop_name

            loop_task = asyncio.create_task(
                chat_custom_loop(client, chat_id, loop_name, current_delay)
            )
            ACTIVE_TARGET_LOOPS[chat_id]["loop_task"] = loop_task
            RUNNING_TASKS.add(loop_task)
            loop_task.add_done_callback(RUNNING_TASKS.discard)

            res = await event.reply(f"🚀 **Loop started for `{loop_name}` with delay `{current_delay}s`!**\nUse `!sloop` to stop.")
            task = asyncio.create_task(schedule_delete(event, res, delay=5))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text == "!sloop" or text.startswith("!sloop "):
            chat_id = event.chat_id
            if chat_id in ACTIVE_TARGET_LOOPS and ACTIVE_TARGET_LOOPS[chat_id].get("loop_active"):
                ACTIVE_TARGET_LOOPS[chat_id]["loop_active"] = False
                res = await event.reply("🛑 **Loop stopped successfully!**")
            else:
                res = await event.reply("ℹ️ **No active loop is running in this chat.**")

            task = asyncio.create_task(schedule_delete(event, res, delay=5))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text.startswith("!dloop "):
            args = event.raw_text.split(maxsplit=1)
            if len(args) < 2 or not args[1].strip().replace('.', '', 1).isdigit():
                res = await event.reply("⚠️ **Usage:** `!dloop <seconds>` (Range: 10s - 100000s)")
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            delay_val = float(args[1].strip())
            if delay_val < 1 or delay_val > 100000:
                res = await event.reply("❌ **Delay must be between 1 and 100000 seconds!**")
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            chat_id = event.chat_id
            if chat_id not in ACTIVE_TARGET_LOOPS:
                ACTIVE_TARGET_LOOPS[chat_id] = {}

            ACTIVE_TARGET_LOOPS[chat_id]["loop_delay"] = delay_val
            res = await event.reply(f"⏱️ **Loop delay updated to `{delay_val}` seconds!**")
            task = asyncio.create_task(schedule_delete(event, res, delay=5))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text.startswith("!join "):
            if not is_primary_bot and SYSTEM_MODE == "eco":
                return

            args = event.raw_text.split(maxsplit=1)
            if len(args) < 2:
                res = await event.reply("⚠️ **Usage:** `!join <group_link_or_username>`")
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            target_link = args[1].strip()
            status_msg = await event.reply(f"⏳ **Joining target group across `{len(ACTIVE_USERBOTS)}` userbot(s)...**")

            joined_count = 0
            failed_count = 0

            private_hash = None
            if "joinchat/" in target_link:
                private_hash = target_link.split("joinchat/")[1].split("/")[0].split("?")[0]
            elif "t.me/+" in target_link:
                private_hash = target_link.split("t.me/+")[1].split("/")[0].split("?")[0]

            async def bot_join_task(ph, bot_cli):
                nonlocal joined_count, failed_count
                try:
                    if private_hash:
                        await bot_cli(functions.messages.ImportChatInviteRequest(hash=private_hash))
                    else:
                        clean_target = target_link.replace("https://t.me/", "").replace("t.me/", "").replace("@", "")
                        entity = await bot_cli.get_entity(clean_target)
                        await bot_cli(functions.channels.JoinChannelRequest(entity))
                    joined_count += 1
                except Exception as join_err:
                    if "USER_ALREADY_PARTICIPANT" in str(join_err):
                        joined_count += 1
                    else:
                        print(f"Join error for bot ({ph}): {join_err}")
                        failed_count += 1

            join_tasks = [bot_join_task(ph, bot_cli) for ph, bot_cli in list(ACTIVE_USERBOTS.items())]
            await asyncio.gather(*join_tasks)

            res_text = (
                f"🎉 **JOIN PROCESS COMPLETED!**\n\n"
                f"✅ **Bots Joined:** `{joined_count}`\n"
                f"❌ **Failed:** `{failed_count}`"
            )
            await status_msg.edit(res_text)
            task = asyncio.create_task(schedule_delete(event, status_msg, delay=10))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text.startswith("!co"):
            if event.sender_id != owner_id:
                res = await event.reply(
                    "❌ **Only the main owner can add co-admins!**"
                )
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            target_user = None
            args = event.raw_text.split(maxsplit=1)

            if reply:
                target_user = await reply.get_sender()
            elif len(args) > 1:
                query = args[1].strip()
                try:
                    if query.lstrip("-").isdigit():
                        target_user = await client.get_entity(int(query))
                    else:
                        target_user = await client.get_entity(query)
                except Exception as e:
                    res = await event.reply(
                        f"❌ **User not found:** `{str(e)}`"
                    )
                    task = asyncio.create_task(
                        schedule_delete(event, res, delay=5)
                    )
                    RUNNING_TASKS.add(task)
                    task.add_done_callback(RUNNING_TASKS.discard)
                    return
            else:
                res = await event.reply(
                    "⚠️ **Usage:** Reply to a user with `!co` OR type `!co"
                    " <username/ID>`"
                )
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            if not target_user:
                res = await event.reply("❌ **Could not resolve user.**")
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            user_id = target_user.id
            user_name = (
                f"{target_user.first_name or ''} {target_user.last_name or ''}".strip()
                or "User"
            )
            username = (
                f"@{target_user.username}"
                if target_user.username
                else "No Username"
            )

            if user_id in config["co_admins"]:
                res = await event.reply(
                    f"⚠️ **{user_name}** (`{user_id}`) is already a Co-Admin."
                )
            else:
                config["co_admins"].append(user_id)
                save_config(config)
                res = await event.reply(
                    "✅ **Co-Admin Added Successfully!**\n\n"
                    f"👤 **Name:** {user_name}\n"
                    f"🆔 **ID:** `{user_id}`\n"
                    f"🏷️ **Username:** {username}\n\n"
                    "💡 *This user can now issue commands to the bot.*"
                )
            task = asyncio.create_task(schedule_delete(event, res, delay=8))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text.startswith("!de"):
            if event.sender_id != owner_id:
                res = await event.reply(
                    "❌ **Only the main owner can remove co-admins!**"
                )
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            target_id = None
            target_name = "User"
            args = event.raw_text.split(maxsplit=1)

            if reply:
                target_id = reply.sender_id
                target_user = await reply.get_sender()
                if target_user:
                    target_name = target_user.first_name or "User"
            elif len(args) > 1:
                query = args[1].strip()
                try:
                    if query.lstrip("-").isdigit():
                        target_id = int(query)
                    else:
                        entity = await client.get_entity(query)
                        target_id = entity.id
                        target_name = entity.first_name or "User"
                except Exception:
                    if query.lstrip("-").isdigit():
                        target_id = int(query)

            if not target_id:
                res = await event.reply(
                    "⚠️ **Usage:** Reply to a user with `!de` OR type `!de"
                    " <username/ID>`"
                )
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            if target_id not in config["co_admins"]:
                res = await event.reply(
                    f"ℹ️ User `{target_id}` is not in the Co-Admin list."
                )
            else:
                config["co_admins"].remove(target_id)
                save_config(config)
                res = await event.reply(
                    "🗑️ **Removed Co-Admin role from:**"
                    f" `{target_name}` (`{target_id}`)"
                )

            task = asyncio.create_task(schedule_delete(event, res, delay=8))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif (
            text == "!colist"
            or text.startswith("!colist ")
            or text == "!listco"
            or text.startswith("!listco ")
        ):
            co_list = config.get("co_admins", [])
            if not co_list:
                res = await event.reply(
                    "ℹ️ **No Co-Admins registered yet.** Add one using `!co"
                    " <user>`."
                )
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            status_msg = await event.reply("📋 **Fetching Co-Admins list...**")
            list_text = "👑 **ACTIVE CO-ADMINS LIST**:\n\n"

            for idx, c_id in enumerate(co_list, 1):
                try:
                    entity = await client.get_entity(c_id)
                    username = (
                        f"@{entity.username}"
                        if entity.username
                        else "No Username"
                    )
                    name = (
                        f"{entity.first_name or ''} {entity.last_name or ''}".strip()
                        or "User"
                    )
                    list_text += (
                        f"**{idx}. {name}**\n   ├ 🆔 ID: `{c_id}`\n   └ 🏷️"
                        f" Username: {username}\n\n"
                    )
                except Exception:
                    list_text += f"**{idx}. User**\n   └ 🆔 ID: `{c_id}`\n\n"

            list_text += (
                "💡 **To remove a co-admin, use:** `!de <ID/Username>`"
            )
            await status_msg.edit(list_text)
            task = asyncio.create_task(
                schedule_delete(event, status_msg, delay=15)
            )
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text.startswith("!add "):
            if event.is_private:
                res = await event.reply(
                    "❌ **This command can only be used in groups/channels!**"
                )
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            args = event.raw_text.split(maxsplit=1)
            if len(args) < 2:
                res = await event.reply(
                    "⚠️ **Usage:** `!add <username / user_id>`"
                )
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            user_input = args[1].strip()
            msg = await event.reply(f"⏳ **Adding user `{user_input}`...**")

            try:
                target = await client.get_entity(
                    int(user_input)
                    if user_input.lstrip("-").isdigit()
                    else user_input
                )
                await client(
                    functions.channels.InviteToChannelRequest(
                        event.chat_id, [target]
                    )
                )
                await msg.edit("✅ **User successfully added to group!**")
            except Exception as e:
                await msg.edit(f"❌ **Failed to add user:** `{str(e)}`")

            task = asyncio.create_task(schedule_delete(event, msg, delay=5))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text.startswith("!promote"):
            if event.is_private:
                res = await event.reply(
                    "❌ **This command can only be used in groups!**"
                )
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            target_user = None
            args = event.raw_text.split(maxsplit=1)

            if reply:
                target_user = await reply.get_sender()
            elif len(args) > 1:
                query = args[1].strip()
                try:
                    target_user = await client.get_entity(
                        int(query) if query.lstrip("-").isdigit() else query
                    )
                except Exception as e:
                    res = await event.reply(
                        f"❌ **User not found:** `{str(e)}`"
                    )
                    task = asyncio.create_task(
                        schedule_delete(event, res, delay=5)
                    )
                    RUNNING_TASKS.add(task)
                    task.add_done_callback(RUNNING_TASKS.discard)
                    return

            if not target_user:
                res = await event.reply(
                    "⚠️ **Usage:** Reply to user with `!promote` OR type"
                    " `!promote <user>`"
                )
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            msg = await event.reply(
                f"⏳ **Promoting `{target_user.first_name}` to Admin...**"
            )
            try:
                admin_rights = ChatAdminRights(
                    change_info=True,
                    delete_messages=True,
                    ban_users=True,
                    invite_users=True,
                    pin_messages=True,
                    add_admins=False,
                    manage_call=True,
                )
                await client(
                    functions.channels.EditAdminRequest(
                        event.chat_id,
                        target_user.id,
                        admin_rights,
                        rank="Admin",
                    )
                )
                await msg.edit(
                    "👑 **Successfully promoted"
                    f" `{target_user.first_name}` to Admin!**"
                )
            except Exception as e:
                await msg.edit(f"❌ **Promotion failed:** `{str(e)}`")

            task = asyncio.create_task(schedule_delete(event, msg, delay=5))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text.startswith("!dmote"):
            if event.is_private:
                res = await event.reply(
                    "❌ **This command can only be used in groups!**"
                )
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            target_user = None
            args = event.raw_text.split(maxsplit=1)

            if reply:
                target_user = await reply.get_sender()
            elif len(args) > 1:
                query = args[1].strip()
                try:
                    target_user = await client.get_entity(
                        int(query) if query.lstrip("-").isdigit() else query
                    )
                except Exception as e:
                    res = await event.reply(
                        f"❌ **User not found:** `{str(e)}`"
                    )
                    task = asyncio.create_task(
                        schedule_delete(event, res, delay=5)
                    )
                    RUNNING_TASKS.add(task)
                    task.add_done_callback(RUNNING_TASKS.discard)
                    return

            if not target_user:
                res = await event.reply(
                    "⚠️ **Usage:** Reply to user with `!dmote` OR type"
                    " `!dmote <user>`"
                )
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            msg = await event.reply(
                f"⏳ **Demoting `{getattr(target_user, 'first_name', 'User')}` from Admin...**"
            )
            try:
                demote_rights = ChatAdminRights(
                    change_info=False,
                    post_messages=False,
                    edit_messages=False,
                    delete_messages=False,
                    ban_users=False,
                    invite_users=False,
                    pin_messages=False,
                    add_admins=False,
                    manage_call=False,
                )
                await client(
                    functions.channels.EditAdminRequest(
                        event.chat_id,
                        target_user.id,
                        demote_rights,
                        rank="",
                    )
                )
                await msg.edit(
                    "📉 **Successfully demoted"
                    f" `{getattr(target_user, 'first_name', 'User')}` to regular member!**"
                )
            except Exception as e:
                await msg.edit(f"❌ **Demotion failed:** `{str(e)}`")

            task = asyncio.create_task(schedule_delete(event, msg, delay=5))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text.startswith("!kick"):
            if event.is_private:
                res = await event.reply(
                    "❌ **This command can only be used in groups!**"
                )
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            target_user = None
            args = event.raw_text.split(maxsplit=1)

            if reply:
                target_user = await reply.get_sender()
            elif len(args) > 1:
                query = args[1].strip()
                try:
                    target_user = await client.get_entity(
                        int(query) if query.lstrip("-").isdigit() else query
                    )
                except Exception as e:
                    res = await event.reply(
                        f"❌ **User not found:** `{str(e)}`"
                    )
                    task = asyncio.create_task(
                        schedule_delete(event, res, delay=5)
                    )
                    RUNNING_TASKS.add(task)
                    task.add_done_callback(RUNNING_TASKS.discard)
                    return

            if not target_user:
                res = await event.reply(
                    "⚠️ **Usage:** Reply to user with `!kick` OR type `!kick"
                    " <user>`"
                )
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            msg = await event.reply(
                f"⏳ **Kicking `{target_user.first_name}`...**"
            )
            try:
                await client(
                    functions.channels.EditBannedRequest(
                        event.chat_id,
                        target_user.id,
                        ChatBannedRights(until_date=None, view_messages=True),
                    )
                )
                await client(
                    functions.channels.EditBannedRequest(
                        event.chat_id,
                        target_user.id,
                        ChatBannedRights(until_date=None),
                    )
                )
                await msg.edit(
                    f"👞 **Kicked `{target_user.first_name}` out of group!**"
                )
            except Exception as e:
                await msg.edit(f"❌ **Kick failed:** `{str(e)}`")

            task = asyncio.create_task(schedule_delete(event, msg, delay=5))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text.startswith("!bmute"):
            if event.is_private:
                res = await event.reply(
                    "❌ **This command can only be used in groups!**"
                )
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            target_user = None
            args = event.raw_text.split(maxsplit=1)

            if reply:
                target_user = await reply.get_sender()
            elif len(args) > 1:
                query = args[1].strip()
                try:
                    target_user = await client.get_entity(
                        int(query) if query.lstrip("-").isdigit() else query
                    )
                except Exception as e:
                    res = await event.reply(
                        f"❌ **User not found:** `{str(e)}`"
                    )
                    task = asyncio.create_task(
                        schedule_delete(event, res, delay=5)
                    )
                    RUNNING_TASKS.add(task)
                    task.add_done_callback(RUNNING_TASKS.discard)
                    return

            if not target_user:
                res = await event.reply(
                    "⚠️ **Usage:** Reply to user with `!bmute` OR type `!bmute"
                    " <user>`"
                )
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            msg = await event.reply(
                "⏳ **Disallowing messages for"
                f" `{target_user.first_name}`...**"
            )
            try:
                mute_rights = ChatBannedRights(
                    until_date=None, send_messages=True
                )
                await client(
                    functions.channels.EditBannedRequest(
                        event.chat_id, target_user.id, mute_rights
                    )
                )
                await msg.edit(
                    f"🔇 **Muted `{target_user.first_name}` from sending"
                    " messages in group!**"
                )
            except Exception as e:
                await msg.edit(f"❌ **Group mute failed:** `{str(e)}`")

            task = asyncio.create_task(schedule_delete(event, msg, delay=5))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text.startswith("!bunmute") or text.startswith("!bolg"):
            if event.is_private:
                res = await event.reply("❌ **This command can only be used in groups!**")
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            target_user = None
            args = event.raw_text.split(maxsplit=1)

            if reply:
                target_user = await reply.get_sender()
            elif len(args) > 1:
                query = args[1].strip()
                try:
                    target_user = await client.get_entity(
                        int(query) if query.lstrip("-").isdigit() else query
                    )
                except Exception as e:
                    res = await event.reply(f"❌ **User not found:** `{str(e)}`")
                    task = asyncio.create_task(schedule_delete(event, res, delay=5))
                    RUNNING_TASKS.add(task)
                    task.add_done_callback(RUNNING_TASKS.discard)
                    return

            if not target_user:
                res = await event.reply("⚠️ **Usage:** Reply to user with `!bunmute` OR type `!bunmute <user>`")
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            msg = await event.reply(f"⏳ **Restoring chat permissions for `{getattr(target_user, 'first_name', 'User')}`...**")
            try:
                unmute_rights = ChatBannedRights(
                    until_date=None,
                    view_messages=False,
                    send_messages=False,
                    send_media=False,
                    send_stickers=False,
                    send_gifs=False,
                    send_games=False,
                    send_inline=False,
                    embed_links=False,
                )
                await client(
                    functions.channels.EditBannedRequest(
                        event.chat_id, target_user.id, unmute_rights
                    )
                )
                await msg.edit(f"🔊 **Successfully restored messaging rights for `{getattr(target_user, 'first_name', 'User')}` in group!**")
            except Exception as e:
                await msg.edit(f"❌ **Group unmute failed:** `{str(e)}`")

            task = asyncio.create_task(schedule_delete(event, msg, delay=5))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text == "!leave" or text.startswith("!leave "):
            if event.is_private:
                res = await event.reply(
                    "❌ **This command can only be used in groups or"
                    " channels!**"
                )
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            try:
                msg = await event.reply("👋 **Leaving group now... Bye!**")
                await asyncio.sleep(1)
                await client(
                    functions.channels.LeaveChannelRequest(event.chat_id)
                )
            except Exception:
                try:
                    await client.delete_dialog(event.chat_id)
                except Exception as e:
                    print(f"Error leaving group: {e}")
            return

        elif text.startswith("!p "):
            args = text.split()
            if len(args) > 1 and args[1].isdigit():
                page_num = int(args[1])
                help_text = build_help_menu(page_num)

                target_msg_id = HELP_MENU_CACHE.get(event.chat_id)
                edited = False

                if target_msg_id:
                    try:
                        await client.edit_message(
                            event.chat_id, target_msg_id, help_text
                        )
                        edited = True
                    except Exception:
                        pass

                if not edited:
                    if reply:
                        try:
                            await reply.edit(help_text)
                            HELP_MENU_CACHE[event.chat_id] = reply.id
                            edited = True
                        except Exception:
                            pass

                    if not edited:
                        new_msg = await event.reply(help_text)
                        HELP_MENU_CACHE[event.chat_id] = new_msg.id

                task = asyncio.create_task(schedule_delete(event, delay=0))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

        elif text.startswith("!help"):
            help_text = build_help_menu(1)
            
            target_msg_id = HELP_MENU_CACHE.get(event.chat_id)
            if target_msg_id:
                try:
                    await client.edit_message(event.chat_id, target_msg_id, help_text)
                    task = asyncio.create_task(schedule_delete(event, delay=0))
                    RUNNING_TASKS.add(task)
                    task.add_done_callback(RUNNING_TASKS.discard)
                    return
                except Exception:
                    pass

            status_msg = await event.reply("⚙️ *Fetching help menu...*")

            mf_url = (
                "https://www.mediafire.com/file/i0tlcm8vbf17do0/photo_2026-07-24_06-40-02.jpg/file"
            )
            img_path = f"help_{int(time.time())}.jpg"
            direct_link = None

            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                    " AppleWebKit/537.36 (KHTML, like Gecko)"
                    " Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "en-US,en;q=0.5",
            }

            try:
                async with get_fast_session(ssl_verify=False) as session:
                    async with session.get(
                        mf_url, headers=headers, timeout=15, allow_redirects=True
                    ) as response:
                        if response.status == 200:
                            html_text = await response.text()
                            match = re.search(
                                r'href="(https?://download\d+\.mediafire\.com/[^"]+)"',
                                html_text,
                            )
                            if match:
                                direct_link = match.group(1)
            except Exception as e:
                print(f"MediaFire Resolution Error: {e}")

            download_success = False
            if direct_link:
                async with get_fast_session(ssl_verify=False) as session:
                    download_success = await download_file_ultra_fast(
                        session, direct_link, img_path, headers=headers
                    )

            try:
                if (
                    download_success
                    and os.path.exists(img_path)
                    and os.path.getsize(img_path) > 0
                ):
                    sent = await event.reply(help_text, file=img_path)
                else:
                    sent = await event.reply(help_text)

                HELP_MENU_CACHE[event.chat_id] = sent.id
            except Exception as e:
                print(f"Failed sending media message: {e}")
                sent = await event.reply(help_text)
                HELP_MENU_CACHE[event.chat_id] = sent.id
            finally:
                if os.path.exists(img_path):
                    try:
                        os.remove(img_path)
                    except Exception:
                        pass
                await status_msg.delete()
            return

        elif text.startswith("!st "):
            token = event.raw_text[4:].strip()
            msg = await event.reply("⚙️ **Connecting Bot Father Token...**")

            if not token:
                await msg.edit("❌ **Usage:** `!st <bot_father_token>`")
                task = asyncio.create_task(schedule_delete(event, msg, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            if token in config["song_bots"]:
                await msg.edit(
                    "⚠️ **This bot token is already added to the system.**"
                )
                task = asyncio.create_task(schedule_delete(event, msg, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            success, res = await start_song_bot_worker(
                config["api_id"], config["api_hash"], token
            )
            if success:
                config["song_bots"].append(token)
                save_config(config)
                await msg.edit(
                    f"✅ **Bot @{res} successfully activated as a Song"
                    " Bot!**\nAnyone can now search & download songs via"
                    f" clickable buttons on @{res}."
                )
            else:
                await msg.edit(f"❌ **Failed to start bot:** `{res}`")

            task = asyncio.create_task(schedule_delete(event, msg, delay=10))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text == "!listst" or text.startswith("!listst "):
            if not ACTIVE_SONG_BOTS:
                msg = await event.reply(
                    "ℹ️ **No active song bots registered.** Add one using `!st"
                    " <token>`."
                )
                task = asyncio.create_task(schedule_delete(event, msg, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            msg = await event.reply("📋 **Fetching active song bots...**")
            bots_text = "🤖 **ACTIVATED SONG BOTS LIST**:\n\n"

            for idx, (username, info) in enumerate(
                ACTIVE_SONG_BOTS.items(), 1
            ):
                u_count = len(config.get("bot_users", {}).get(username, []))
                bots_text += (
                    f"**{idx}.** @{username}\n   ├ 🆔 Bot ID:"
                    f" `{info['bot_id']}`\n   └ 👥 Users Served: `{u_count}`\n\n"
                )

            bots_text += (
                "💡 **To remove a bot, use:** `!rem <username or list_number>`"
            )
            await msg.edit(bots_text)
            task = asyncio.create_task(
                schedule_delete(event, msg, delay=10)
            )
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text.startswith("!rem "):
            target = event.raw_text[5:].strip().lower().replace("@", "")
            msg = await event.reply(
                "⏳ **Processing removal & broadcasting notice for:**"
                f" `{target}`..."
            )

            if not ACTIVE_SONG_BOTS:
                await msg.edit("⚠️ **No active song bots to remove.**")
                task = asyncio.create_task(schedule_delete(event, msg, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            selected_username = None

            if target.isdigit():
                idx = int(target) - 1
                keys = list(ACTIVE_SONG_BOTS.keys())
                if 0 <= idx < len(keys):
                    selected_username = keys[idx]
            else:
                if target in ACTIVE_SONG_BOTS:
                    selected_username = target

            if (
                not selected_username
                or selected_username not in ACTIVE_SONG_BOTS
            ):
                await msg.edit(
                    f"❌ **Bot `{target}` not found in active list.** Check"
                    " `!listst`."
                )
                task = asyncio.create_task(schedule_delete(event, msg, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            bot_info = ACTIVE_SONG_BOTS[selected_username]
            bot_client = bot_info["client"]
            token = bot_info["token"]

            bot_users = config.get("bot_users", {}).get(selected_username, [])

            removal_msg = "⚠️ This bot has been removed from system"
            sent_count = 0

            if bot_users:
                await msg.edit(
                    "📢 **Broadcasting removal message to"
                    f" {len(bot_users)} users...**"
                )

                async def send_notice(uid):
                    nonlocal sent_count
                    try:
                        await bot_client.send_message(uid, removal_msg)
                        sent_count += 1
                    except (UserIsBlockedError, PeerIdInvalidError, Exception):
                        pass

                tasks = [send_notice(uid) for uid in bot_users]
                await asyncio.gather(*tasks)

            try:
                await bot_client.send_message(
                    owner_id,
                    f"⚠️ **Bot @{selected_username} has been removed from the"
                    f" system.**\n📢 Notified `{sent_count}/{len(bot_users)}`"
                    " active users.",
                )
            except Exception as e:
                print(f"Could not send removal log: {e}")

            try:
                await bot_client.disconnect()
                bot_info["task"].cancel()
            except Exception:
                pass

            del ACTIVE_SONG_BOTS[selected_username]
            if token in config["song_bots"]:
                config["song_bots"].remove(token)
            if selected_username in config.get("bot_users", {}):
                del config["bot_users"][selected_username]
            save_config(config)

            await msg.edit(
                f"🗑️ **Successfully removed @{selected_username}!**\n📢 Sent"
                f" removal message to `{sent_count}` users."
            )
            task = asyncio.create_task(schedule_delete(event, msg, delay=5))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text == "!ping" or text.startswith("!ping "):
            start_time = time.perf_counter()
            msg = await event.reply("🏓 **Pinging...**")
            end_time = time.perf_counter()
            latency = (end_time - start_time) * 1000

            await msg.edit(
                "🏓 **Pong!**\n"
                f"⚡ **Latency:** `{latency:.2f} ms`\n"
                "🚀 **Status:** `Online & Ready`"
            )

            task = asyncio.create_task(schedule_delete(event, msg, delay=5))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text.startswith("!speedtest") or text == "!speed":
            status_msg = await event.reply(
                "🚀 **Running speed test...**\n*This may take 10-15 seconds.*"
            )

            start_time = time.perf_counter()
            try:
                data = await asyncio.to_thread(perform_speedtest)
                elapsed = time.perf_counter() - start_time

                result_text = (
                    "📊 **SPEEDTEST RESULTS**\n\n"
                    f"📥 **Download:** `{data['download']:.2f} Mbps`\n"
                    f"📤 **Upload:** `{data['upload']:.2f} Mbps`\n"
                    f"⚡ **Ping / Latency:** `{data['ping']:.2f} ms`\n\n"
                    f"🏢 **ISP:** `{data['isp']}` (`{data['client_ip']}`)\n"
                    f"🌍 **Server:** `{data['sponsor']}` -"
                    f" `{data['server_name']}, {data['server_country']}`\n"
                    f"⏱️ **Test Duration:** `{elapsed:.2f}s`"
                )
                await status_msg.edit(result_text)

            except Exception as e:
                await status_msg.edit(f"❌ **Speedtest Failed:** `{str(e)}`")

            task = asyncio.create_task(
                schedule_delete(event, status_msg, delay=15)
            )
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text.startswith("!1 "):
            query = event.raw_text[3:].strip()

            if not query:
                res = await event.reply("❌ Usage: `!1 <song name>`")
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            status_msg = await event.reply(f"⚡ Searching: `{query}`...")

            success, results = await search_music_all(query)
            if not success or not results:
                await status_msg.edit(f"❌ {results}")
                task = asyncio.create_task(
                    schedule_delete(event, status_msg, delay=5)
                )
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            song = results[0]
            audio_path = None

            try:
                song_name = song.get("name", query)
                artist_names = song.get("artists", "Unknown Artist")
                quality_urls = song.get("quality_urls", [])

                song_url = quality_urls[0]["url"] if quality_urls else song.get("preview_url")

                if not song_url:
                    await status_msg.edit(
                        f"❌ No audio URL for **{song_name}**."
                    )
                    task = asyncio.create_task(
                        schedule_delete(event, status_msg, delay=5)
                    )
                    RUNNING_TASKS.add(task)
                    task.add_done_callback(RUNNING_TASKS.discard)
                    return

                timestamp = int(time.time())
                audio_path = f"song_{timestamp}.mp3"

                await status_msg.edit(
                    f"🎵 **{song_name}**\n"
                    f"🎤 **Artist:** {artist_names}\n\n"
                    "⚡ **Fast Downloading...**"
                )

                async with get_fast_session() as http_sess:
                    dl_success = await download_file_ultra_fast(
                        http_sess, song_url, audio_path
                    )

                if not dl_success or not os.path.exists(audio_path):
                    await status_msg.edit("❌ Failed downloading song file.")
                    task = asyncio.create_task(
                        schedule_delete(event, status_msg, delay=5)
                    )
                    RUNNING_TASKS.add(task)
                    task.add_done_callback(RUNNING_TASKS.discard)
                    return

                audio_attr = DocumentAttributeAudio(
                    duration=0,
                    title=song_name,
                    performer=artist_names,
                )

                caption = f"🎵 **{song_name}**\n🎤 **Artist:** {artist_names}"

                await client.send_file(
                    event.chat_id,
                    audio_path,
                    caption=caption,
                    attributes=[audio_attr],
                    reply_to=event.id,
                )

                task = asyncio.create_task(
                    schedule_delete(event, status_msg, delay=5)
                )
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)

            except Exception as e:
                await status_msg.edit(f"❌ Error: {str(e)}")
                task = asyncio.create_task(
                    schedule_delete(event, status_msg, delay=5)
                )
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)

            finally:
                if audio_path and os.path.exists(audio_path):
                    os.remove(audio_path)
            return

        elif text.startswith("!tts "):
            parts = event.raw_text[5:].strip().split(" ", 1)
            if len(parts) < 2:
                res = await event.reply(
                    "❌ Usage: `!tts <male/female> <text>`"
                )
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            gender = parts[0].lower()
            text_to_speak = parts[1].strip()

            status_msg = await event.reply("🎙️ **Converting text to speech...**")
            success, result, voice_used = await text_to_speech(
                gender, text_to_speak
            )

            if success and os.path.exists(result):
                try:
                    await client.send_file(
                        event.chat_id,
                        result,
                        caption=f"🎙️ Voice: {gender.upper()}",
                        reply_to=event.id,
                    )
                    os.remove(result)
                    task = asyncio.create_task(
                        schedule_delete(event, status_msg, delay=5)
                    )
                    RUNNING_TASKS.add(task)
                    task.add_done_callback(RUNNING_TASKS.discard)
                except Exception as e:
                    await status_msg.edit(f"❌ Failed: {str(e)[:100]}")
                    task = asyncio.create_task(
                        schedule_delete(event, status_msg, delay=5)
                    )
                    RUNNING_TASKS.add(task)
                    task.add_done_callback(RUNNING_TASKS.discard)
            else:
                await status_msg.edit("❌ Failed to generate speech")
                task = asyncio.create_task(
                    schedule_delete(event, status_msg, delay=5)
                )
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text.startswith("!img "):
            prompt = event.raw_text[5:].strip()
            if not prompt:
                res = await event.reply("❌ Usage: `!img <description>`")
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            status_msg = await event.reply("🎨 Generating image...")
            success, result = await generate_image(prompt)

            if success and os.path.exists(result):
                try:
                    await client.send_file(
                        event.chat_id,
                        result,
                        caption=f"🎨 Prompt: {prompt}",
                        reply_to=event.id,
                    )
                    os.remove(result)
                    task = asyncio.create_task(
                        schedule_delete(event, status_msg, delay=5)
                    )
                    RUNNING_TASKS.add(task)
                    task.add_done_callback(RUNNING_TASKS.discard)
                except Exception as e:
                    await status_msg.edit(f"❌ Failed: {str(e)[:100]}")
                    task = asyncio.create_task(
                        schedule_delete(event, status_msg, delay=5)
                    )
                    RUNNING_TASKS.add(task)
                    task.add_done_callback(RUNNING_TASKS.discard)
            else:
                await status_msg.edit("❌ Failed to generate image")
                task = asyncio.create_task(
                    schedule_delete(event, status_msg, delay=5)
                )
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text.startswith("!chat "):
            question = event.raw_text[6:].strip()
            if not question:
                res = await event.reply("❌ Usage: `!chat <question>`")
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            status_msg = await event.reply("💬 Thinking...")
            success, response = await get_ai_response(question)

            if success:
                await status_msg.edit(
                    f"💬 **AI Response**\n\n{response[:3900]}"
                )
                task = asyncio.create_task(
                    schedule_delete(event, status_msg, delay=5)
                )
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
            else:
                await status_msg.edit(f"❌ Failed: {response}")
                task = asyncio.create_task(
                    schedule_delete(event, status_msg, delay=5)
                )
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text == "!purge" or text.startswith("!purge "):
            args = text.split()
            if reply:
                msg = await event.reply("🧹 **Purging messages in range...**")
                try:
                    start_msg_id = reply.id
                    end_msg_id = event.id

                    messages_to_delete = []
                    async for message in client.iter_messages(
                        event.chat_id,
                        min_id=start_msg_id - 1,
                        max_id=end_msg_id + 1,
                    ):
                        messages_to_delete.append(message.id)

                    if messages_to_delete:
                        for i in range(0, len(messages_to_delete), 100):
                            await client.delete_messages(
                                event.chat_id, messages_to_delete[i : i + 100]
                            )

                    status = await event.respond(
                        "✅ **Purged"
                        f" `{len(messages_to_delete)}` messages.**"
                    )
                    task = asyncio.create_task(
                        schedule_delete(status, delay=3)
                    )
                    RUNNING_TASKS.add(task)
                    task.add_done_callback(RUNNING_TASKS.discard)

                except Exception as e:
                    err = await event.reply(f"❌ **Purge failed:** `{str(e)}`")
                    task = asyncio.create_task(
                        schedule_delete(err, msg, delay=5)
                    )
                    RUNNING_TASKS.add(task)
                    task.add_done_callback(RUNNING_TASKS.discard)
                return

            elif len(args) > 1 and args[1].isdigit():
                count = int(args[1])
                if count <= 0:
                    res = await event.reply(
                        "❌ **Please specify a count greater than 0.**"
                    )
                    task = asyncio.create_task(
                        schedule_delete(event, res, delay=5)
                    )
                    RUNNING_TASKS.add(task)
                    task.add_done_callback(RUNNING_TASKS.discard)
                    return

                msg = await event.reply(
                    f"🧹 **Purging last {count} messages...**"
                )
                try:
                    messages_to_delete = []
                    async for message in client.iter_messages(
                        event.chat_id, limit=count + 2
                    ):
                        messages_to_delete.append(message.id)

                    if messages_to_delete:
                        for i in range(0, len(messages_to_delete), 100):
                            await client.delete_messages(
                                event.chat_id, messages_to_delete[i : i + 100]
                            )

                    status = await event.respond(
                        "✅ **Successfully purged"
                        f" `{len(messages_to_delete) - 2}` messages.**"
                    )
                    task = asyncio.create_task(
                        schedule_delete(status, delay=3)
                    )
                    RUNNING_TASKS.add(task)
                    task.add_done_callback(RUNNING_TASKS.discard)

                except Exception as e:
                    err = await event.reply(f"❌ **Purge failed:** `{str(e)}`")
                    task = asyncio.create_task(
                        schedule_delete(err, msg, delay=5)
                    )
                    RUNNING_TASKS.add(task)
                    task.add_done_callback(RUNNING_TASKS.discard)
                return

            else:
                res = await event.reply(
                    "⚠️ **Usage:** Reply to a message with `!purge` OR type"
                    " `!purge <count>`"
                )
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

        elif text.startswith("!bdc"):
            if event.sender_id != owner_id and event.sender_id not in co_admins:
                res = await event.reply("❌ **Unauthorized:** Only admins can use this command.")
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            args = text.split()
            if len(args) < 2 or not args[1].isdigit():
                res = await event.reply("⚠️ **Usage:** `!bdc <count>`\n*Example:* `!bdc 5`")
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            count = int(args[1])
            if count <= 0:
                res = await event.reply("❌ **Please specify a count greater than 0.**")
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            status_msg = await event.reply(f"⚡ **Fast-fetching last `{count}` messages for backup...**")
            
            chat = await event.get_chat()
            chat_title = getattr(chat, 'title', None) or getattr(chat, 'first_name', 'Private Chat')
            chat_username = f"@{chat.username}" if getattr(chat, 'username', None) else f"ID: `{event.chat_id}`"
            
            temp_backup_dir = "bdc_backup"
            os.makedirs(temp_backup_dir, exist_ok=True)

            try:
                log_header = (
                    "📦 **MEDIA BACKUP LOG (!bdc)**\n\n"
                    f"🏷️ **Chat Name:** {chat_title}\n"
                    f"🔗 **Chat Username/ID:** {chat_username}\n"
                    f"📥 **Requested Limit:** `{count}`\n"
                    "━━━━━━━━━━━━━━━━━━━"
                )
                await client.send_message(owner_id, log_header)

                messages = await client.get_messages(event.chat_id, limit=count)
                media_messages = [msg for msg in messages if msg.media]

                if not media_messages:
                    await status_msg.edit("ℹ️ **No media found within the last specified messages.**")
                    task = asyncio.create_task(schedule_delete(event, status_msg, delay=5))
                    RUNNING_TASKS.add(task)
                    task.add_done_callback(RUNNING_TASKS.discard)
                    return

                await status_msg.edit(f"🚀 **Downloading & uploading `{len(media_messages)}` media file(s) concurrently...**")

                async def process_media_item(message):
                    try:
                        file_path = await message.download_media(file=temp_backup_dir)
                        if file_path and os.path.exists(file_path):
                            caption = (
                                f"📎 **Recovered Media Item**\n"
                                f"💬 **From Chat:** {chat_title} (`{event.chat_id}`)\n"
                                f"👤 **Sender ID:** `{message.sender_id}`\n"
                                f"⏱️ **Date:** `{message.date}`"
                            )
                            await client.send_file(owner_id, file_path, caption=caption)
                            try:
                                os.remove(file_path)
                            except Exception:
                                pass
                            return True
                    except Exception as item_err:
                        print(f"Concurrent backup error for message {message.id}: {item_err}")
                    return False

                results = await asyncio.gather(*(process_media_item(msg) for msg in media_messages))
                saved_files_count = sum(1 for success in results if success)

                await status_msg.edit(
                    f"✅ **High-Speed Backup Complete!**\n"
                    f"Successfully transferred `{saved_files_count}` media file(s) to owner chat."
                )

            except Exception as e:
                await status_msg.edit(f"❌ **Backup failed:** `{str(e)}`")

            task = asyncio.create_task(schedule_delete(event, status_msg, delay=8))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text.startswith("!clone") and reply:
            user = await reply.get_sender()
            msg = await event.reply("⚡ Copying profile...")

            photo_path = await client.download_profile_photo(
                user, file="clone.jpg"
            )
            full = await client(functions.users.GetFullUserRequest(user.id))
            bio = full.full_user.about or ""

            await client(
                functions.account.UpdateProfileRequest(
                    first_name=user.first_name or "",
                    last_name=user.last_name or "",
                    about=bio,
                )
            )

            if photo_path and os.path.exists(photo_path):
                try:
                    file = await client.upload_file(photo_path)
                    await client(
                        functions.photos.UploadProfilePhotoRequest(file=file)
                    )
                except Exception:
                    pass

            await msg.edit("✅ Cloned successfully!")
            task = asyncio.create_task(schedule_delete(event, msg, delay=5))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)

        elif text.startswith("!res"):
            msg = await event.reply("♻️ Restoring profile...")

            await client(
                functions.account.UpdateProfileRequest(
                    first_name=me.first_name or "",
                    last_name=me.last_name or "",
                    about="",
                )
            )

            photos = await client(
                functions.photos.GetUserPhotosRequest(
                    user_id="me", offset=0, max_id=0, limit=1
                )
            )

            if photos.photos:
                await client(
                    functions.photos.DeletePhotosRequest(id=photos.photos)
                )

            await msg.edit("✅ Profile restored!")
            task = asyncio.create_task(schedule_delete(event, msg, delay=5))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)

        elif text.startswith("!id") and reply:
            res = await reply.reply(f"👤 User ID: {reply.sender_id}")
            task = asyncio.create_task(schedule_delete(event, res, delay=5))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)

        elif text.startswith("!del") and reply:
            await reply.delete()
            await event.delete()

        elif text.startswith("!cud") and reply:
            user = await reply.get_sender()
            TARGET_USER = user.id
            CUD_ACTIVE = True
            res = await event.reply(f"🔥 CUD started on: {user.first_name}")
            task = asyncio.create_task(schedule_delete(event, res, delay=5))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)

        elif text.startswith("!ruk"):
            CUD_ACTIVE = False
            TARGET_USER = None
            res = await event.reply("🛑 CUD stopped!")
            task = asyncio.create_task(schedule_delete(event, res, delay=5))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)

        elif text.startswith("!allmute"):
            ALL_MUTE_CHATS.add(event.chat_id)
            res = await event.reply("🔇 **All mute activated for this chat!**")
            task = asyncio.create_task(schedule_delete(event, res, delay=5))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)

        elif text.startswith("!abbolo"):
            if event.chat_id in ALL_MUTE_CHATS:
                ALL_MUTE_CHATS.remove(event.chat_id)
            res = await event.reply(
                "🔊 **All mute deactivated for this chat!**"
            )
            task = asyncio.create_task(schedule_delete(event, res, delay=5))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)

        elif text.startswith("!for"):
            if not reply:
                res = await event.reply(
                    "⚠️ **Usage:** Reply to any message with `!for` to start"
                    " continuous forwarding."
                )
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            chat_id = event.chat_id

            if (
                chat_id in ACTIVE_TARGET_LOOPS
                and ACTIVE_TARGET_LOOPS[chat_id].get("forward_active")
            ):
                ACTIVE_TARGET_LOOPS[chat_id]["forward_active"] = False
                await asyncio.sleep(0.5)

            target_msg_id = reply.id

            async def message_forward_loop(cli, target_chat, msg_id):
                while (
                    target_chat in ACTIVE_TARGET_LOOPS
                    and ACTIVE_TARGET_LOOPS[target_chat].get("forward_active")
                ):
                    try:
                        await cli.forward_messages(
                            target_chat, msg_id, target_chat
                        )
                    except Exception as e:
                        print(
                            f"Forward Loop Error in chat {target_chat}: {e}"
                        )
                    await asyncio.sleep(1.5)

            loop_task = asyncio.create_task(
                message_forward_loop(client, chat_id, target_msg_id)
            )
            RUNNING_TASKS.add(loop_task)
            loop_task.add_done_callback(RUNNING_TASKS.discard)

            ACTIVE_TARGET_LOOPS[chat_id] = {
                "forward_active": True,
                "task": loop_task,
            }

            res = await event.reply(
                "🔄 **Message forwarding loop started in this chat!**\nType"
                " `!sfor` to stop."
            )
            task = asyncio.create_task(schedule_delete(event, res, delay=5))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text == "!sfor" or text.startswith("!sfor "):
            chat_id = event.chat_id

            if (
                chat_id not in ACTIVE_TARGET_LOOPS
                or not ACTIVE_TARGET_LOOPS[chat_id].get("forward_active")
            ):
                res = await event.reply(
                    "ℹ️ **No active message forward loop running in this"
                    " chat.**"
                )
            else:
                ACTIVE_TARGET_LOOPS[chat_id]["forward_active"] = False
                res = await event.reply(
                    "🛑 **Message forwarding loop stopped for this chat!**"
                )

            task = asyncio.create_task(schedule_delete(event, res, delay=5))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text.startswith("!live"):
            args = text.split(" ", 1)
            if len(args) < 2:
                res = await event.reply(
                    "⚠️ **Usage:** `!live <your text>` or reply to a message"
                    " with `!live <your text>`"
                )
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            slide_text = args[1].strip()
            chat_id = event.chat_id

            if chat_id in ACTIVE_TARGET_LOOPS and ACTIVE_TARGET_LOOPS[
                chat_id
            ].get("slide_active"):
                ACTIVE_TARGET_LOOPS[chat_id]["slide_active"] = False
                await asyncio.sleep(0.5)

            if reply:
                msg_to_slide = await event.reply(f"✨ **{slide_text}** ✨")
            else:
                msg_to_slide = await client.send_message(
                    chat_id, f"✨ **{slide_text}** ✨"
                )
                try:
                    await event.delete()
                except Exception:
                    pass

            pinned_successfully = False
            try:
                await client.pin_message(
                    chat_id, msg_to_slide.id, notify=True
                )
                pinned_successfully = True
            except Exception as e:
                print(
                    "Pin validation failed (check admin rights in chat"
                    f" {chat_id}): {e}"
                )

            async def text_slide_loop(
                target_msg, raw_text, target_chat, was_pinned
            ):
                frames = [
                    f"📌 ✨ **{raw_text}** ✨",
                    f"📌 🚀 **{raw_text}** 🚀",
                    f"📌 ⚡ **{raw_text}** ⚡",
                    f"📌 🔥 **{raw_text}** 🔥",
                    f"📌 💥 **{raw_text}** 💥",
                ]
                frame_idx = 1

                while (
                    target_chat in ACTIVE_TARGET_LOOPS
                    and ACTIVE_TARGET_LOOPS[target_chat].get("slide_active")
                ):
                    try:
                        await target_msg.edit(frames[frame_idx % len(frames)])
                        frame_idx += 1
                    except Exception as e:
                        print(
                            "Slide loop warning in chat"
                            f" {target_chat}: {e}"
                        )
                        if "MESSAGE_ID_INVALID" in str(
                            e
                        ) or "Message author required" in str(e):
                            break
                    await (
                        asyncio.sleep(1.5)
                    )

                if was_pinned:
                    try:
                        await client.unpin_message(target_chat, target_msg.id)
                    except Exception as e:
                        print(
                            "Failed to unpin sliding message in chat"
                            f" {target_chat}: {e}"
                        )

            if chat_id not in ACTIVE_TARGET_LOOPS:
                ACTIVE_TARGET_LOOPS[chat_id] = {}

            ACTIVE_TARGET_LOOPS[chat_id]["slide_active"] = True
            ACTIVE_TARGET_LOOPS[chat_id]["slide_msg_id"] = msg_to_slide.id

            loop_task = asyncio.create_task(
                text_slide_loop(
                    msg_to_slide, slide_text, chat_id, pinned_successfully
                )
            )
            ACTIVE_TARGET_LOOPS[chat_id]["slide_task"] = loop_task
            RUNNING_TASKS.add(loop_task)
            loop_task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text == "!ss" or text.startswith("!ss "):
            chat_id = event.chat_id

            if (
                chat_id not in ACTIVE_TARGET_LOOPS
                or not ACTIVE_TARGET_LOOPS[chat_id].get("slide_active")
            ):
                res = await event.reply(
                    "ℹ️ **No active text loop running in this chat.**"
                )
            else:
                ACTIVE_TARGET_LOOPS[chat_id]["slide_active"] = False
                res = await event.reply(
                    "🛑 **Text stopped and pinned message released!**"
                )

            task = asyncio.create_task(schedule_delete(event, res, delay=5))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)
            return

        elif text.startswith("!chup") and reply:
            user_id = reply.sender_id
            if user_id == owner_id:
                res = await event.reply("❌ Cannot mute owner.")
            else:
                MUTED_USERS.add(user_id)
                res = await event.reply(f"🔇 User `{user_id}` muted.")
            task = asyncio.create_task(schedule_delete(event, res, delay=5))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)

        elif text.startswith("!bol"):
            args = event.raw_text.split(maxsplit=1)

            if reply:
                user_id = reply.sender_id
                if user_id in MUTED_USERS:
                    MUTED_USERS.remove(user_id)
                    res = await event.reply(f"🔊 User `{user_id}` unmuted.")
                else:
                    res = await event.reply("ℹ️ User is not muted.")
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)

            elif len(args) > 1:
                target_input = args[1].strip()
                target_id = None

                try:
                    entity = await client.get_entity(
                        target_input
                        if not target_input.lstrip("-").isdigit()
                        else int(target_input)
                    )
                    target_id = entity.id
                except Exception:
                    if target_input.lstrip("-").isdigit():
                        target_id = int(target_input)

                if target_id and target_id in MUTED_USERS:
                    MUTED_USERS.remove(target_id)
                    res = await event.reply(
                        f"🔊 User `{target_input}` (ID: `{target_id}`)"
                        " unmuted."
                    )
                else:
                    res = await event.reply(
                        f"ℹ️ User `{target_input}` is not in the muted list."
                    )
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)

            else:
                if not MUTED_USERS:
                    res = await event.reply(
                        "🔊 **No users are currently muted.**"
                    )
                    task = asyncio.create_task(
                        schedule_delete(event, res, delay=5)
                    )
                    RUNNING_TASKS.add(task)
                    task.add_done_callback(RUNNING_TASKS.discard)
                else:
                    msg = await event.reply(
                        "📋 **Fetching muted users list...**"
                    )
                    muted_list_text = "🔇 **MUTED USERS LIST**:\n\n"

                    for u_id in list(MUTED_USERS):
                        try:
                            entity = await client.get_entity(u_id)
                            username = (
                                f"@{entity.username}"
                                if entity.username
                                else "No Username"
                            )
                            name = (
                                f"{entity.first_name or ''} {entity.last_name or ''}".strip()
                                or "User"
                            )
                            muted_list_text += (
                                f"👤 **{name}**\n├ 🆔 ID: `{u_id}`\n└ 🏷️"
                                f" User: {username}\n\n"
                            )
                        except Exception:
                            muted_list_text += (
                                f"👤 **User**\n└ 🆔 ID: `{u_id}`\n\n"
                            )

                    muted_list_text += (
                        "💡 **Please select a user to unmute:**\nReply to their"
                        " message with `!bol` OR type:\n`!bol <username or"
                        " chat_id>`"
                    )
                    await msg.edit(muted_list_text)
                    task = asyncio.create_task(
                        schedule_delete(event, msg, delay=10)
                    )
                    RUNNING_TASKS.add(task)
                    task.add_done_callback(RUNNING_TASKS.discard)

        elif text.startswith("!floodbypass"):
            args = text.split()
            if len(args) >= 2:
                if args[1] == "on":
                    FLOOD_BYPASS = True
                    client.flood_sleep_threshold = 0
                    res = await event.reply("⚡ Flood bypass ENABLED")
                elif args[1] == "off":
                    FLOOD_BYPASS = False
                    client.flood_sleep_threshold = 60
                    res = await event.reply("🛡️ Flood bypass DISABLED")
                else:
                    res = await event.reply("Usage: `!floodbypass on/off`")
            else:
                res = await event.reply(
                    f"Flood bypass: {'ON' if FLOOD_BYPASS else 'OFF'}"
                )
            task = asyncio.create_task(schedule_delete(event, res, delay=5))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)

        elif text.startswith("!find") and event.sender_id == owner_id:
            args = event.raw_text.split(maxsplit=1)
            if len(args) < 2:
                res = await event.reply(
                    "⚠️ Usage: `!find <user ID / username / phone number>`"
                )
                task = asyncio.create_task(schedule_delete(event, res, delay=5))
                RUNNING_TASKS.add(task)
                task.add_done_callback(RUNNING_TASKS.discard)
                return

            query = args[1].strip()
            msg = await event.reply("🔎 Looking up user...")

            try:
                if query.lstrip("-").isdigit():
                    entity_id = int(query)
                    entity = await client.get_entity(entity_id)
                else:
                    entity = await client.get_entity(query)

                username = (
                    f"@{entity.username}" if entity.username else "No username"
                )
                name = (
                    f"{entity.first_name or ''} {entity.last_name or ''}".strip()
                    or "No name"
                )

                reply_text = (
                    f"✅ User found\nName: {name}\nID: {entity.id}\nUsername:"
                    f" {username}"
                )
                await msg.edit(reply_text)

            except Exception as e:
                await msg.edit(f"❌ Error: {str(e)}")

            task = asyncio.create_task(schedule_delete(event, msg, delay=5))
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)


# ==============================================================================
# VOICE CHAT / AUDIO PLAYBACK PROCESSOR
# ==============================================================================
async def setup_voice_call_engine(phone, client):
    if not HAS_PYTGCALLS:
        return None

    existing = VOICE_CALLS.get(phone)
    if existing is not None:
        return existing

    try:
        call = PyTgCalls(client)
        res = call.start()
        if asyncio.iscoroutine(res):
            await res
        VOICE_CALLS[phone] = call
        print(f"🔊 Voice-call engine ready for {phone}")
        return call
    except Exception as e:
        print(f"❌ Failed to start PyTgCalls for {phone}: {e}")
        return None


def _safe_remove_file(path):
    if not path:
        return
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        print(f"⚠️ Could not remove voice file {path}: {e}")


def get_silent_audio_path():
    silent_path = "silent_cue.mp3"
    if not os.path.exists(silent_path):
        try:
            subprocess.run([
                "ffmpeg", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", 
                "-t", "5", "-q:a", "9", "-y", silent_path
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except Exception:
            pass
    return silent_path if os.path.exists(silent_path) else None


async def join_voice_call_all(event):
    if not HAS_PYTGCALLS:
        await event.reply("❌ **Voice playback is not installed.**")
        return

    if event.is_private:
        res = await event.reply("❌ **This command can only be used in groups!**")
        task = asyncio.create_task(schedule_delete(event, res, delay=5))
        RUNNING_TASKS.add(task)
        task.add_done_callback(RUNNING_TASKS.discard)
        return

    chat_id = event.chat_id
    status_msg = await event.reply(f"🚀 **Connecting `{len(ACTIVE_USERBOTS)}` userbot(s) to voice chat successfully...**")

    silent_file = get_silent_audio_path()
    success_count = 0
    async def join_single_bot(phone, client_obj):
        nonlocal success_count
        call = VOICE_CALLS.get(phone)
        if call:
            try:
                if silent_file and os.path.exists(silent_file):
                    await call.play(chat_id, silent_file)
                elif hasattr(call, "join_group_call"):
                    await call.join_group_call(chat_id)
                elif hasattr(call, "join_call"):
                    await call.join_call(chat_id)
                success_count += 1
            except Exception as e:
                print(f"Silent join error for bot {phone}: {e}")

    tasks = [join_single_bot(phone, client_obj) for phone, client_obj in ACTIVE_USERBOTS.items()]
    await asyncio.gather(*tasks)

    await status_msg.edit(f"✅ **Successfully joined voice chat with `{success_count}` userbot(s)!**")
    task = asyncio.create_task(schedule_delete(status_msg, delay=6))
    RUNNING_TASKS.add(task)
    task.add_done_callback(RUNNING_TASKS.discard)


async def start_vcopy_feature(event, client, phone_number):
    if not HAS_PYTGCALLS:
        await event.reply("❌ **Voice playback/py-tgcalls is not installed.** Run: `pip install -U py-tgcalls`")
        return

    if event.is_private:
        res = await event.reply("❌ **This command can only be used in groups!**")
        task = asyncio.create_task(schedule_delete(event, res, delay=5))
        RUNNING_TASKS.add(task)
        task.add_done_callback(RUNNING_TASKS.discard)
        return

    chat_id = event.chat_id
    status_msg = await event.reply("🎙️ **Initiating VCOPY mode... Joining voice chat with all bots successfully...**")

    silent_file = get_silent_audio_path()
    joined_count = 0
    for ph, bot_cli in ACTIVE_USERBOTS.items():
        call = VOICE_CALLS.get(ph)
        if call:
            try:
                if silent_file and os.path.exists(silent_file):
                    await call.play(chat_id, silent_file)
                elif hasattr(call, "join_group_call"):
                    await call.join_group_call(chat_id)
                elif hasattr(call, "join_call"):
                    await call.join_call(chat_id)
                joined_count += 1
            except Exception as e:
                print(f"VCOPY join error for {ph}: {e}")

    ACTIVE_VCOPY_SESSIONS[chat_id] = {"active": True}
    await status_msg.edit(
        f"✅ **VCOPY Activated!**\n"
        f"🔊 Connected `{joined_count}` bots to voice chat successfully.\n"
        f"🎤 Listening to Admin voice & broadcasting across all bots. Type `!endc` to stop."
    )
    task = asyncio.create_task(schedule_delete(status_msg, delay=8))
    RUNNING_TASKS.add(task)
    task.add_done_callback(RUNNING_TASKS.discard)


async def play_replied_audio(event, phone, reply):
    if not HAS_PYTGCALLS:
        await event.reply("❌ **Voice playback is not installed.**\nRun: `pip install -U py-tgcalls`")
        return

    if not reply:
        await event.reply("⚠️ **Reply to an audio/voice file with `!play` or `!vcl`.**")
        return

    mime = (getattr(reply.file, "mime_type", None) or "").lower()
    is_audio = bool(getattr(reply, "audio", None) or getattr(reply, "voice", None))
    if not is_audio and not mime.startswith("audio/"):
        await event.reply("❌ **The replied message is not an audio/voice file.**")
        return

    call = VOICE_CALLS.get(phone)
    if not call:
        await event.reply("❌ Voice engine is not running.")
        return

    chat_id = event.chat_id
    timestamp = int(time.time() * 1000)
    ext = ""
    original_name = getattr(getattr(reply, "file", None), "name", None)
    if original_name and "." in original_name:
        ext = os.path.splitext(original_name)[1].lower()
    if not ext:
        ext = ".ogg" if getattr(reply, "voice", None) else ".mp3"

    audio_path = os.path.abspath(f"voice_raw_{abs(int(chat_id))}_{timestamp}{ext}")
    status = await event.reply("⬇️ **Downloading audio file...**")

    try:
        downloaded = await reply.download_media(file=audio_path)
        if not downloaded or not os.path.exists(audio_path):
            await status.edit("❌ **Failed to download the replied audio.**")
            _safe_remove_file(audio_path)
            return

        if chat_id in ACTIVE_VOICE_LOOPS:
            ACTIVE_VOICE_LOOPS[chat_id]["active"] = False
            await asyncio.sleep(0.1)

        ACTIVE_VOICE_LOOPS[chat_id] = {"active": True}
        VOICE_CALL_FILES[(phone, chat_id)] = audio_path

        audio_attr = getattr(reply, "audio", None) or getattr(reply, "voice", None)
        duration_secs = getattr(audio_attr, "duration", 0) if audio_attr else 0

        if duration_secs <= 0:
            try:
                cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_path]
                output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode().strip()
                duration_secs = float(output)
            except Exception:
                duration_secs = 60

        await status.edit(f"⚡ **Instant Loop Active!** (Length: `{duration_secs:.1f}s`)\nUse `!endc` to stop.")

        async def exact_audio_loop_worker():
            while chat_id in ACTIVE_VOICE_LOOPS and ACTIVE_VOICE_LOOPS[chat_id].get("active"):
                try:
                    if hasattr(call, "join_group_call"):
                        try:
                            await call.join_group_call(chat_id)
                        except Exception:
                            pass
                    await call.play(chat_id, audio_path)
                    start_time = time.time()
                    while chat_id in ACTIVE_VOICE_LOOPS and ACTIVE_VOICE_LOOPS[chat_id].get("active"):
                        if (time.time() - start_time) >= duration_secs:
                            break
                        await asyncio.sleep(0.05)
                except Exception as e:
                    print(f"Exact loop error in chat {chat_id}: {e}")
                    await asyncio.sleep(0.5)

        loop_task = asyncio.create_task(exact_audio_loop_worker())
        RUNNING_TASKS.add(loop_task)
        loop_task.add_done_callback(RUNNING_TASKS.discard)
        ACTIVE_VOICE_LOOPS[chat_id]["task"] = loop_task

    except Exception as e:
        _safe_remove_file(audio_path)
        await status.edit(f"❌ **Voice playback error:** `{str(e)[:500]}`")


async def play_loop_all_userbots(event, reply):
    if not HAS_PYTGCALLS:
        await event.reply("❌ **Voice playback is not installed.**")
        return

    if not reply:
        await event.reply("⚠️ **Reply to an audio/voice file with `!rvc`.**")
        return

    mime = (getattr(reply.file, "mime_type", None) or "").lower()
    is_audio = bool(getattr(reply, "audio", None) or getattr(reply, "voice", None))
    if not is_audio and not mime.startswith("audio/"):
        await event.reply("❌ **The replied message is not an audio/voice file.**")
        return

    if not ACTIVE_USERBOTS:
        await event.reply("❌ **No active userbots connected.**")
        return

    chat_id = event.chat_id
    timestamp = int(time.time() * 1000)
    ext = ""
    original_name = getattr(getattr(reply, "file", None), "name", None)
    if original_name and "." in original_name:
        ext = os.path.splitext(original_name)[1].lower()
    if not ext:
        ext = ".ogg" if getattr(reply, "voice", None) else ".mp3"

    audio_path = os.path.abspath(f"rvc_raw_{abs(int(chat_id))}_{timestamp}{ext}")
    status = await event.reply("⬇️ **Downloading audio for all bots instant playback...**")

    try:
        downloaded = await reply.download_media(file=audio_path)
        if not downloaded or not os.path.exists(audio_path):
            await status.edit("❌ **Failed to download the audio file.**")
            _safe_remove_file(audio_path)
            return

        if chat_id in ACTIVE_VOICE_LOOPS:
            ACTIVE_VOICE_LOOPS[chat_id]["active"] = False
            await asyncio.sleep(0.1)

        ACTIVE_VOICE_LOOPS[chat_id] = {"active": True}

        audio_attr = getattr(reply, "audio", None) or getattr(reply, "voice", None)
        duration_secs = getattr(audio_attr, "duration", 0) if audio_attr else 0
        if duration_secs <= 0:
            try:
                cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_path]
                output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode().strip()
                duration_secs = float(output)
            except Exception:
                duration_secs = 60

        async def single_bot_exact_worker(phone, call_obj, ch_id, a_path):
            while chat_id in ACTIVE_VOICE_LOOPS and ACTIVE_VOICE_LOOPS[chat_id].get("active"):
                try:
                    if hasattr(call_obj, "join_group_call"):
                        try:
                            await call_obj.join_group_call(ch_id)
                        except Exception:
                            pass
                    await call_obj.play(ch_id, a_path)
                    start_time = time.time()
                    while chat_id in ACTIVE_VOICE_LOOPS and ACTIVE_VOICE_LOOPS[chat_id].get("active"):
                        if (time.time() - start_time) >= duration_secs:
                            break
                        await asyncio.sleep(0.05)
                except Exception as e:
                    print(f"RVC exact loop error for {phone} in chat {ch_id}: {e}")
                    await asyncio.sleep(0.5)

        bot_tasks = []
        for phone, client_obj in ACTIVE_USERBOTS.items():
            call = VOICE_CALLS.get(phone)
            if call:
                t = asyncio.create_task(single_bot_exact_worker(phone, call, chat_id, audio_path))
                RUNNING_TASKS.add(t)
                t.add_done_callback(RUNNING_TASKS.discard)
                bot_tasks.append(t)

        VOICE_CALL_FILES[("all", chat_id)] = audio_path

        await status.edit(f"⚡ **Instant exact loop playing across `{len(bot_tasks)}` userbot(s).\nUse `!endc` to stop.**")

    except Exception as e:
        _safe_remove_file(audio_path)
        await status.edit(f"❌ **RVC playback error:** `{str(e)[:500]}`")


async def end_voice_call_all(event):
    chat_id = event.chat_id
    if chat_id in ACTIVE_VOICE_LOOPS:
        ACTIVE_VOICE_LOOPS[chat_id]["active"] = False
        del ACTIVE_VOICE_LOOPS[chat_id]

    if chat_id in ACTIVE_VCOPY_SESSIONS:
        ACTIVE_VCOPY_SESSIONS[chat_id]["active"] = False
        del ACTIVE_VCOPY_SESSIONS[chat_id]

    success_count = 0
    for phone, call in VOICE_CALLS.items():
        try:
            await asyncio.wait_for(call.leave_call(chat_id), timeout=10)
            success_count += 1
        except Exception:
            pass

    cleanup_keys = [("all", chat_id)]
    for phone in list(VOICE_CALL_FILES.keys()):
        if isinstance(phone, tuple) and len(phone) > 1 and phone[1] == chat_id:
            cleanup_keys.append(phone)
        elif isinstance(phone, str) and phone != "all":
            cleanup_keys.append((phone, chat_id))

    for key in cleanup_keys:
        path = VOICE_CALL_FILES.pop(key, None)
        _safe_remove_file(path)

    await event.reply(f"🛑 **Stopped loop, disconnected all calls, & cleaned up temporary files (`{success_count}` accounts left).**")


async def start_userbot_instance(api_id, api_hash, phone):
    phone_clean = re.sub(r"\D", "", phone)
    session_file = os.path.join(SESSIONS_DIR, f"userbot_{phone_clean}")

    client = TelegramClient(session_file, api_id, api_hash)

    try:
        await client.connect()
        if not await client.is_user_authorized():
            print(f"⚠️ Session expired or unauthenticated for {phone}.")
            return False

        attach_userbot_handlers(client, phone)

        me = await client.get_me()
        print(f"✅ Userbot Active on Account: {me.first_name} ({phone})")

        ACTIVE_USERBOTS[phone] = client
        await setup_voice_call_engine(phone, client)

        task = asyncio.create_task(client.run_until_disconnected())
        RUNNING_TASKS.add(task)
        task.add_done_callback(RUNNING_TASKS.discard)
        return True

    except Exception as e:
        print(f"❌ Error launching userbot instance: {e}")
        return False


# Setup Control Bot Handlers with Interactive Setup & Session Checker Buttons
def setup_control_bot_handlers():
    global CONTROL_CLIENT

    @CONTROL_CLIENT.on(events.NewMessage(pattern="/start"))
    async def control_start(event):
        buttons = [
            [Button.inline("🚀 New Setup", data="setup_new")],
            [Button.inline("📂 See Session Available or Not", data="setup_check_session")]
        ]
        await event.reply(
            "⚡ **XNS Main Control Panel**\n\n"
            "Welcome! Please choose an option below:",
            buttons=buttons
        )

    @CONTROL_CLIENT.on(events.CallbackQuery)
    async def control_callback(event):
        data = event.data.decode("utf-8")
        sender_id = event.sender_id

        if data == "setup_new":
            SETUP_STATES[sender_id] = {"step": "WAITING_PASSWORD"}
            await event.edit(
                "🔐 **Security Check:**\n\n"
                "Please enter your bot setup password to begin configuration:",
                buttons=None
            )

        elif data == "setup_check_session":
            sessions = [f for f in os.listdir(SESSIONS_DIR) if f.endswith(".session") or not "." in f]
            if sessions:
                buttons = [
                    [Button.inline("🚀 Run Code with Old Session", data="run_old")],
                    [Button.inline("🗑️ Clear Old Session", data="clear_old_session")]
                ]
                await event.edit(
                    f"📂 **Session Status:** Found `{len(sessions)}` saved session(s) in `{SESSIONS_DIR}/` directory.\n\n"
                    "Choose an action:",
                    buttons=buttons
                )
            else:
                buttons = [[Button.inline("🚀 Start New Setup", data="setup_new")]]
                await event.edit(
                    "ℹ️ **Session Status:** No active sessions found.\n\n"
                    "Please click below to start setup:",
                    buttons=buttons
                )

        elif data == "clear_old_session":
            try:
                for f in os.listdir(SESSIONS_DIR):
                    if f.endswith(".session") or not "." in f:
                        os.remove(os.path.join(SESSIONS_DIR, f))
                cfg = load_config()
                cfg["user_phones"] = []
                save_config(cfg)
                await event.edit(
                    "🗑️ **Old sessions cleared successfully!**\n\n"
                    "Click below to start a new setup:",
                    buttons=[[Button.inline("🚀 Start New Setup", data="setup_new")]]
                )
            except Exception as e:
                await event.edit(f"❌ Error clearing sessions: {e}")

        elif data == "run_old":
            await event.edit("🚀 **Starting system with existing sessions...**", buttons=None)
            config = load_config()
            saved_phones = config.get("user_phones", [])
            for phone in saved_phones:
                if phone not in ACTIVE_USERBOTS:
                    asyncio.create_task(start_userbot_instance(config["api_id"], config["api_hash"], phone))
            await event.respond("✅ **System running successfully with old sessions!** Use `/bots` or `/status` to verify.")

    @CONTROL_CLIENT.on(events.NewMessage)
    async def control_interactive_handler(event):
        sender_id = event.sender_id
        if sender_id not in SETUP_STATES:
            text = event.raw_text.strip().lower()
            if text == "/bots":
                if not ACTIVE_USERBOTS:
                    await event.reply("ℹ️ No active userbots running.")
                    return
                txt = "🤖 **Active Userbots:**\n\n"
                for idx, (ph, cli) in enumerate(ACTIVE_USERBOTS.items(), 1):
                    try:
                        me = await cli.get_me()
                        txt += f"{idx}. {me.first_name} (`{ph}`)\n"
                    except Exception:
                        txt += f"{idx}. (`{ph}`)\n"
                await event.reply(txt)
            elif text.startswith("/dc "):
                target = event.raw_text[4:].strip()
                found = None
                for ph in ACTIVE_USERBOTS.keys():
                    if target in ph: found = ph; break
                if found:
                    await ACTIVE_USERBOTS[found].disconnect()
                    del ACTIVE_USERBOTS[found]
                    cfg = load_config()
                    if found in cfg["user_phones"]: cfg["user_phones"].remove(found); save_config(cfg)
                    await event.reply(f"✅ Disconnected `{found}`")
                else:
                    await event.reply("❌ Session not found.")
            elif text == "/status":
                await event.reply(f"📊 Uptime: `{get_readable_time(time.time() - START_TIME)}`\nActive Userbots: `{len(ACTIVE_USERBOTS)}`")
            return

        state_info = SETUP_STATES[sender_id]
        step = state_info["step"]
        val = event.raw_text.strip()

        if step == "WAITING_PASSWORD":
            config = load_config()
            correct_pwd = config.get("bot_password", "xns")
            if val == correct_pwd:
                state_info["step"] = "WAITING_OWNER_ID"
                await event.reply(
                    "✅ **Password Correct!**\n\n"
                    "👉 Please enter **Owner Chat ID** for use userbot as owner:"
                )
            else:
                await event.reply("❌ **Incorrect Password!** Please try again:")

        elif step == "WAITING_OWNER_ID":
            if val.lstrip("-").isdigit():
                owner_id = int(val)
                config = load_config()
                config["owner_id"] = owner_id
                save_config(config)
                state_info["step"] = "WAITING_PHONE"
                await event.reply(
                    "✅ **Owner ID Saved!**\n\n"
                    "👉 Now, enter your **Primary Phone Number** (with country code, e.g., `+919876543210`):"
                )
            else:
                await event.reply("❌ Please enter a valid numeric Telegram Chat ID:")

        elif step == "WAITING_PHONE":
            phone = re.sub(r"[^\d+]", "", val)
            if phone.startswith("+") and len(phone) > 8:
                config = load_config()
                config["phone"] = phone
                if phone not in config["user_phones"]:
                    config["user_phones"].append(phone)
                save_config(config)

                status_msg = await event.reply(f"📡 Sending OTP request to `{phone}`...")
                temp_session = os.path.join(SESSIONS_DIR, f"userbot_{re.sub(r'\D', '', phone)}")
                temp_client = TelegramClient(temp_session, config["api_id"], config["api_hash"])

                try:
                    await temp_client.connect()
                    res = await temp_client.send_code_request(phone)
                    state_info["client"] = temp_client
                    state_info["phone"] = phone
                    state_info["phone_code_hash"] = res.phone_code_hash
                    state_info["step"] = "WAITING_OTP"
                    await status_msg.edit(f"📩 OTP sent to `{phone}`!\n\n👉 Please reply with the **OTP Code**:")
                except Exception as e:
                    await status_msg.edit(f"❌ Failed to send OTP: {e}\nTry again with `/start`.")
                    del SETUP_STATES[sender_id]
                    await temp_client.disconnect()
            else:
                await event.reply("❌ Invalid format. Please enter a full phone number with country code (e.g. `+91...`):")

        elif step == "WAITING_OTP":
            otp = re.sub(r"\D", "", val)
            if otp:
                temp_client = state_info["client"]
                phone = state_info["phone"]
                try:
                    await temp_client.sign_in(phone, otp, phone_code_hash=state_info["phone_code_hash"])
                    await temp_client.disconnect()
                    del SETUP_STATES[sender_id]

                    config = load_config()
                    asyncio.create_task(start_userbot_instance(config["api_id"], config["api_hash"], phone))
                    await event.reply("🎉 **Setup Complete & Login Successful!**\nYour primary userbot is now online and running.")
                except SessionPasswordNeededError:
                    state_info["step"] = "WAITING_2FA"
                    await event.reply("🔐 **2FA Password Required!**\n\nPlease reply with your 2FA Cloud Password:")
                except Exception as e:
                    await event.reply(f"❌ Sign-In Error: {e}\nRestart setup with `/start`.")
                    del SETUP_STATES[sender_id]
                    await temp_client.disconnect()
            else:
                await event.reply("❌ Please enter a valid numeric OTP code:")

        elif step == "WAITING_2FA":
            password = val
            if password:
                temp_client = state_info["client"]
                phone = state_info["phone"]
                try:
                    await temp_client.sign_in(password=password)
                    await temp_client.disconnect()
                    del SETUP_STATES[sender_id]

                    config = load_config()
                    asyncio.create_task(start_userbot_instance(config["api_id"], config["api_hash"], phone))
                    await event.reply("🎉 **2FA Verified & Setup Complete!**\nYour primary userbot is now online and running.")
                except Exception as e:
                    await event.reply(f"❌ 2FA Error: {e}\nRestart setup with `/start`.")
                    del SETUP_STATES[sender_id]
                    await temp_client.disconnect()
            else:
                await event.reply("❌ Please enter your 2FA password:")


async def main():
    global CONTROL_CLIENT
    config = load_config()
    api_id = config.get("api_id", 25121973)
    api_hash = config.get("api_hash", "d9a7c8ce0b699cf8d93115cf6bf51cad")

    print("🚀 Initializing Permanent XNS Control Bot with Interactive Setup & Session Checker...")
    CONTROL_CLIENT = TelegramClient(os.path.join(SESSIONS_DIR, "control_bot_session"), api_id, api_hash)
    await CONTROL_CLIENT.start(bot_token=CONTROL_BOT_TOKEN)
    setup_control_bot_handlers()
    print("✅ Control Bot Online! Terminal is now free. Manage everything via Telegram.")

    saved_phones = config.get("user_phones", [])
    userbot_tasks = []

    for phone in saved_phones:
        if phone not in ACTIVE_USERBOTS:
            print(f"🔄 Auto-starting saved Userbot session: {phone}...")
            userbot_tasks.append(
                start_userbot_instance(api_id, api_hash, phone)
            )

    if userbot_tasks:
        await asyncio.gather(*userbot_tasks)

    saved_bots = config.get("song_bots", [])
    if saved_bots:
        print(f"🤖 Initializing {len(saved_bots)} saved Helper Song Bots...")
        for b_token in saved_bots:
            task = asyncio.create_task(
                start_song_bot_worker(api_id, api_hash, b_token)
            )
            RUNNING_TASKS.add(task)
            task.add_done_callback(RUNNING_TASKS.discard)

    print("🚀 System Online and ready for commands!")

    # Keep alive via control bot
    try:
        await CONTROL_CLIENT.run_until_disconnected()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        for k, path in list(VOICE_CALL_FILES.items()):
            ph = k[0] if isinstance(k, tuple) else k
            call = VOICE_CALLS.get(ph)
            if call is not None:
                try:
                    chat_id = k[1] if isinstance(k, tuple) and len(k) > 1 else None
                    if chat_id and isinstance(chat_id, int):
                        await asyncio.wait_for(call.leave_call(chat_id), timeout=5)
                except Exception:
                    pass
            _safe_remove_file(path)
            VOICE_CALL_FILES.pop(k, None)

        for ph, cli in list(ACTIVE_USERBOTS.items()):
            if cli.is_connected():
                await cli.disconnect()


if __name__ == "__main__":
    asyncio.main(main()) if hasattr(asyncio, 'main') else asyncio.run(main())
