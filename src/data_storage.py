import asyncio
import json
from pathlib import Path
import re

SRC_DIR = Path(__file__).resolve().parent
DATA_DIR = SRC_DIR.parent / "data"
DATA_FILE = DATA_DIR / "user_ids.json"
DATA_LOCK = asyncio.Lock()

STEAM_ID_DELTA = 76561197960265728

# Regex Patterns
STEAM_ID64 = re.compile(r"^7656119\d{10}$")
STEAM_ID3 = re.compile(r"^\[?U:1:(\d+)\]?$")
STEAM_URL = re.compile(r"profiles/(7656119\d{10})(?:/|$)")

def verify_data_exists():
    try:
        Path(DATA_DIR).mkdir(exist_ok=True)
        with open(DATA_FILE, "x", encoding="utf-8") as file:
            json.dump({}, file)
    except FileExistsError:
        pass

async def save_user(discord_id: int | str, steam_id: str) -> bool:
    async with DATA_LOCK:
        data = {}
        steam_id_available = True

        # Reading json to a dictionary
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                data = {}

        for key, value in data.items():
            if value == steam_id:
                steam_id_available = False

        # Create new entry / Update existing entry
        if steam_id_available:
            data[str(discord_id)] = str(steam_id)

        # Writing dictionary to json
        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

        return steam_id_available

async def get_user(discord_id: int | str):
    async with DATA_LOCK:
        data = {}

        # Reading json to a dictionary
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                data = {}

        return data.get(str(discord_id))

def parse_steam_id(steam_id: str):
    input = steam_id.strip()

    url_match = STEAM_URL.search(input)
    if url_match:
        return url_match.group(1)

    id64_match = STEAM_ID64.search(input)
    if id64_match:
        return id64_match.group(0)

    id3_match = STEAM_ID3.search(input)
    if id3_match:
        return id3_match.group(1)

    return None

def create_steam_id32(steam_id: str):
    if len(steam_id) == 17:
        steam_id32 = int(steam_id) - STEAM_ID_DELTA
        return str(steam_id32)
    else:
        return steam_id

def create_steam_id3(steam_id32: str):
    return f'[U:1:{steam_id32}]'