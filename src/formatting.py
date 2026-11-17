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