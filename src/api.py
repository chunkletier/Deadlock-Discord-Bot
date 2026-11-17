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

MATCH_MODES = {
    0: "Invalid",
    1: "Unranked",
    2: "Private Lobby",
    3: "Co-op Bot Match",
    4: "Ranked",
    5: "Server Test",
    6: "Tutorial",
    7: "Hero Labs",
    8: "New Player Placement"
}

GAME_MODES = {
    0: "Invalid",
    1: "Standard",
    2: "1v1 Test",
    3: "Sandbox",
    4: "Street Brawl",
    5: "Explore NYC",
    6: "Internal",
    7: "Internal 02"
}

def get_match_type(game_mode: int, match_mode: int) -> str:
    if match_mode in [0, 4, 5, 6, 7, 8]:
        return MATCH_MODES.get(match_mode, "")
    if game_mode in [0, 3, 5]:
        return GAME_MODES.get(game_mode, "")

    if match_mode == 1:
        return GAME_MODES.get(game_mode, "")

async def get_player_data(match_id: int, account_id: int) -> dict | None:
    match_metadata = await make_request(f"/v1/matches/{match_id}/metadata")

    if not match_metadata:
        return None

    match_info = match_metadata.get("match_info")
    players = match_info.get("players")
    winning_team = match_info.get("winning_team")

    for player in players:
        if player.get("account_id") == int(account_id):
            player_team = player.get("team")
            return {
                "metadata": player,
                "team": player_team,
                "won": player_team == winning_team,
                "stats": player.get("stats")[-1],
                "net_worth": player.get("net_worth"),
                "mvp_rank": player.get("mvp_rank"),
                "kills": player.get("kills"),
                "deaths": player.get("deaths"),
                "assists": player.get("assists"),
                "player_damage": player.get("stats")[-1].get("player_damage"),
                "boss_damage": player.get("stats")[-1].get("boss_damage"),
                "player_healing": player.get("stats")[-1].get("player_healing"),
                "items": player.get("items")
            }

    return None

async def get_all_items() -> list[dict] | None:
    return await make_request("/v1/assets/items/by-type/upgrade")

async def get_item_icon_url(item_id: int) -> str | None:
    item = await make_request(f"/v1/assets/items/{item_id}")
    return item.get("shop_image")