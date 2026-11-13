import aiohttp

# Eventually replace 'return None' with an exception
async def make_request(directory: str, parameters: dict | None = None):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.deadlock-api.com{directory}",
            params=parameters
        ) as response:
            if response.status != 200:
                return None
            return await response.json()

def get_match_type(game_mode: int, match_mode: int) -> str:
    game_type = ""
    match_type = ""

    match match_mode:
        case 0:
            match_type = "Invalid"
            return match_type
        case 1:
            match_type = "Unranked"
        case 2:
            match_type = "Private Lobby"
        case 3:
            match_type = "Co-op Bot Match"
        case 4:
            match_type = "Ranked"
            return match_type
        case 5:
            match_type = "Server Test"
            return match_type
        case 6:
            match_type = "Tutorial"
            return match_type
        case 7:
            match_type = "Hero Labs"
            return match_type
        case 8:
            match_type = "New Player Placement"
            return match_type

    match game_mode:
        case 0:
            game_type = "Invalid"
            return game_type
        case 1:
            game_type = "Standard"
        case 2:
            game_type = "1v1 Test"
        case 3:
            game_type = "Sandbox"
            return game_type
        case 4:
            game_type = "Street Brawl"
        case 5:
            game_type = "Explore NYC"
            return game_type
        case 6:
            game_type = "Internal"
        case 7:
            game_type = "Internal 02"

    if match_mode == 1:
        return game_type
    else:
        return match_type + game_type

async def match_won(match_id: int, account_id: int) -> list | None:
    metadata = await make_request(f"/v1/matches/{match_id}/metadata", None)
    match_info = metadata.get("match_info")
    winning_team = match_info.get("winning_team")
    players = match_info.get("players")

    for player in players:
        if player.get("account_id") == int(account_id):
            player_team = player.get("team")
            return [winning_team == player_team, player_team]

    return None

async def get_kda(match_id: int, account_id: int) -> list:
    metadata = await make_request(f"/v1/matches/{match_id}/metadata", None)
    match_info = metadata.get("match_info")
    players = match_info.get("players")

    for player in players:
        if player.get("account_id") == int(account_id):
            return [player.get("kills"), player.get("deaths"), player.get("assists")]

    return [0, 0, 0]