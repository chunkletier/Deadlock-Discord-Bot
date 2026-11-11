import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv
from data_storage import *

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
    response_message = ''

    if steam_id != None:
        response_message = f'Your Steam ID32 is `{steam_id}`.'
    else:
        response_message = 'You are not linked to a Steam account. Please link your Steam ID using `/link [steam_id]`.'

    await interaction.followup.send(response_message)

# Adds the command associated with the given function.
bot.tree.add_command(link)
bot.tree.add_command(stats)


bot.run(DISCORD_TOKEN)