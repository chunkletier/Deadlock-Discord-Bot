import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

bot: commands.Bot = commands.Bot(command_prefix=None, intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

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
    #     print(f'Error syncing commands:')

@app_commands.command(name='link', description="Syncs a user to a given Steam ID.")
async def link(interaction: discord.Interaction, steam_id: int):
    await interaction.response.send_message(f'This is the {interaction.command.name} command.\nArgument is {steam_id}.', ephemeral=True)

@app_commands.command(name='stats', description="Returns the stats of the user's most recent Deadlock match. Must be linked.")
async def stats(interaction: discord.Interaction):
    await interaction.response.send_message(f'This is the {interaction.command.name} command.', ephemeral=True)

# Adds the command associated with the given function.
bot.tree.add_command(link)
bot.tree.add_command(stats)


bot.run(DISCORD_TOKEN)