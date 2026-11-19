import discord
import api
import aiohttp
from pathlib import Path

emojis: dict[str, str] = {}

def pad_string(input, width: int = 10) -> str:
    return str(input).ljust(width)

def number_suffix(num) -> str:
    match str(num):
        case "1":
            return "1st"
        case "2":
            return "2nd"
        case "3":
            return "3rd"
        case _:
            return f"{str(num)}th"

def format_thousands(num: int) -> str:
    if num < 1000:
        return str(num)
    else:
        return f"{num / 1000 : .0f}k"

async def get_emoji(emoji: str) -> str:
    return emojis.get(emoji, "\u2754")

async def get_item_emoji(item_id: int, bot: discord.Client) -> str:
    key = f"item_{item_id}"

    if key in emojis:
        return emojis.get(key, "\u2754")

    url = await api.get_item_icon_url(item_id)
    if not url:
        return "\u2754"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                return "\u2754"
            image_bytes = await response.read()

    new_emoji = await bot.create_application_emoji(name=key, image=image_bytes)
    emojis[key] = str(new_emoji)
    return emojis.get(key, "\u2754")

def format_emoji_list(emoji_list: list) -> str:
    formatted_list = [[], []]

    emoji_list_str = ""

    for index, value in enumerate(emoji_list):
        formatted_list[index % 2].append(emoji_list[index])

    for half in formatted_list:
        emoji_list_str += "# "
        for emoji in half:
            emoji_list_str += f"{emoji}\u2002"
        emoji_list_str += "\n"
    # Removes extra newline at the end
    emoji_list_str = emoji_list_str[:-1]

    return emoji_list_str

def get_image_file(file_name: str) -> discord.File:
    SRC_DIR = Path(__file__).resolve().parent
    ASSETS_DIR = SRC_DIR.parent / "assets"
    ASSETS_FILE = ASSETS_DIR / file_name

    return discord.File(ASSETS_FILE, filename=file_name)