import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv
from data_storage import *
import api
import formatting

load_dotenv()

intents = discord.Intents.default()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

bot: commands.Bot = commands.Bot(command_prefix=None, intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

    verify_file_exists()

    # Caution:
    # This syncs new commands to each server with the bot.
    # Running the following code repeatedly can get the bot rate limited.
    # Be careful with the frequency at which you sync your commands.

    # Note:
    # Updating the command implementation does NOT require re-syncing.
    # Only run for new commands or updated definitions.

    # try:
    #     synced = await bot.tree.sync()
    #     print(f'Synced {len(synced)} command(s)')
    # except Exception as e:
    #     print(f'Error syncing commands: {e}')

@app_commands.command(name='link', description="Syncs a user to a given Steam ID.")
async def link(interaction: discord.Interaction, steam_id: str):
    # Allows more time for the function to execute before Discord times out the bot.
    await interaction.response.defer(ephemeral=True)

    steam_id32 = ''
    response_message = ''

    if parse_steam_id(steam_id) != None:
        steam_id32 = create_steam_id32(parse_steam_id(steam_id))
        response_message = f'Linked Discord account to Steam ID `{parse_steam_id(steam_id)}`.\n-# (Steam ID32 `{steam_id32}`)'
        await save_user(interaction.user.id, steam_id32)
    else:
        response_message = 'Invalid Steam ID. Please enter a valid SteamID64, SteamID3, or ID-containing profile link.'

    await interaction.followup.send(response_message)

@app_commands.command(name='stats', description="Returns the stats of the user's most recent Deadlock match. Must be linked.")
async def stats(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    steam_id = await get_user(interaction.user.id)

    # Eventually improve handling None values and exceptions
    if steam_id is not None:
        last_match = (await api.make_request(f"/v1/players/{create_steam_id3(steam_id)}/match-history"))[0]
        match_id = last_match.get("match_id")
        hero_id = last_match.get("hero_id")
        hero_data = await api.make_request(f"/v1/assets/heroes/{hero_id}")
        hero_name = hero_data.get("name")
        hero_cards = {
            "normal": hero_data.get("images").get("icon_hero_card"),
            "critical": hero_data.get("images").get("hero_card_critical"),
            "gloat": hero_data.get("images").get("hero_card_gloat")
        }
        match_winner = await api.match_won(match_id, steam_id)
        match_won = match_winner[0] if match_winner is not None else None
        outcome = "Deadlock"
        colour = discord.Colour.ash_embed()
        hero_card = hero_cards["normal"]

        if match_won is not None:
            if match_won:
                outcome = "Victory"
                colour = discord.Colour.brand_green()
                hero_card = hero_cards["gloat"]
            else:
                outcome = "Defeat"
                colour = discord.Colour.brand_red()
                hero_card = hero_cards["critical"]

        kda = await api.get_kda(match_id, steam_id)

        description = f"{hero_name} - {outcome}"
        embed = discord.Embed(
            title=f"{api.get_match_type(last_match.get("game_mode"), last_match.get("match_mode"))}",
            description=description,
            colour=colour
        )
        embed.set_thumbnail(url=hero_card)
        # embed.add_field(name="K/D/A", value=f"`{kda[0]} / {kda[1]} / {kda[2]}`", inline=True)
        embed.add_field(name="Kills", value=f"`{formatting.pad_string(kda[0])}`", inline=True)
        embed.add_field(name="Deaths", value=f"`{formatting.pad_string(kda[1])}`", inline=True)
        embed.add_field(name="Assists", value=f"`{formatting.pad_string(kda[2])}`", inline=True)


        # response_message = f'Your Steam ID32 is `{steam_id}`.'
        # response_message += f'\nThe last hero you played (`ID: {hero_id}`) was {hero_name}.'
        await interaction.followup.send(embed=embed)
    else:
        response_message = 'You are not linked to a Steam account. Please link your Steam ID using `/link [steam_id]`.'
        await interaction.followup.send(response_message)

    # await interaction.followup.send(response_message,embed=embed)

# Adds the command associated with the given function.
bot.tree.add_command(link)
bot.tree.add_command(stats)


bot.run(DISCORD_TOKEN)