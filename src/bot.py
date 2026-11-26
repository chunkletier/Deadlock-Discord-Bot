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

bot: commands.Bot = commands.Bot(command_prefix=commands.when_mentioned, intents=discord.Intents.all(),
                                 allowed_contexts=app_commands.AppCommandContext(guild=True, dm_channel=True, private_channel=True))

emojis = {}

async def setup_hook():
    app_emojis = await bot.fetch_application_emojis()
    formatting.emojis = {emoji.name: str(emoji) for emoji in app_emojis}
    verify_data_exists()

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
    #     print(f'Error syncing commands: {e}')

@app_commands.command(name='link', description="Syncs a user to a given Steam ID.")
async def link(interaction: discord.Interaction, steam_id: str):
    # Allows more time for the function to execute before Discord times out the bot.
    await interaction.response.defer(ephemeral=True)

    # If SteamID is valid
    if parse_steam_id(steam_id) != None:
        steam_id32 = create_steam_id32(parse_steam_id(steam_id))
        # If SteamID is available
        if (await save_user(interaction.user.id, steam_id32)):
            response_message = f'Linked Discord account to Steam ID `{parse_steam_id(steam_id)}`.\n-# (Steam ID32 `{steam_id32}`)'
        else:
            response_message = f'Steam ID already linked to an account.'
    else:
        response_message = 'Invalid Steam ID. Please enter a valid SteamID64, SteamID3, or ID-containing profile link.'

    await interaction.followup.send(response_message)

@app_commands.command(name='stats', description="Returns the stats of the user's most recent Deadlock match. Must be linked.")
async def stats(interaction: discord.Interaction, public: bool = False):
    await interaction.response.defer(ephemeral=not public)

    steam_id = await get_user(interaction.user.id)

    match_history = (await api.make_request(f"/v1/players/{create_steam_id3(steam_id)}/match-history"))

    if steam_id is not None and len(match_history) != 0:
        # Retrieving last match
        last_match = (await api.make_request(f"/v1/players/{create_steam_id3(steam_id)}/match-history"))[0]
        match_id = last_match.get("match_id")

        # Retrieving hero info
        hero_id = last_match.get("hero_id")
        hero_info = await api.make_request(f"/v1/assets/heroes/{hero_id}")
        hero_name = hero_info.get("name")
        hero_cards = {
            "normal": hero_info.get("images").get("icon_hero_card"),
            "critical": hero_info.get("images").get("hero_card_critical"),
            "gloat": hero_info.get("images").get("hero_card_gloat")
        }

        # Getting user's data from last match
        player_data = await api.get_player_data(match_id, steam_id)
        match_won = player_data.get("won")

        # Default embed params
        outcome = "Deadlock"
        colour = discord.Colour.ash_embed()
        hero_card = hero_cards["normal"]

        # Formatting embed params for win/loss
        if match_won is not None:
            if match_won:
                outcome = "Victory"
                colour = discord.Colour.brand_green()
                hero_card = hero_cards["gloat"]
            else:
                outcome = "Defeat"
                colour = discord.Colour.brand_red()
                hero_card = hero_cards["critical"]

        # Default MVP data
        mvp_rank = player_data.get("mvp_rank")
        mvp_title = ""
        mvp_image = None
        mvp_image_name = ""

        # Formatting match duration into minutes and seconds
        match_duration_s = player_data.get("stats").get("time_stamp_s")
        minutes, seconds = divmod(match_duration_s, 60)

        # Formatting MVP data
        if mvp_rank is not None:
            if mvp_rank == 1:
                mvp_title = "MVP"
                mvp_image_name = "mvp_trophy.png"
                mvp_image = formatting.get_image_file("mvp_trophy.png")
            else:
                mvp_title = "Key Player"
                mvp_image_name = "key_player_trophy.png"
                mvp_image = formatting.get_image_file("key_player_trophy.png")

        # Creating item ID list from owned items
        items = player_data.get("items")
        item_id_list = []

        for item in items:
            item_id = item.get("item_id")
            item_info = await api.make_request(f"/v1/assets/items/{item_id}")
            item_type = item_info.get("type")
            sold_time = item.get("sold_time_s")
            if item_type == "upgrade" and sold_time == 0:
                item_id_list.append(item.get("item_id"))

        # Create emoji list from item id list
        item_emoji_list = [await formatting.get_item_emoji(item_id, bot) for item_id in item_id_list]

        # Creating embed description
        souls_emoji = await formatting.get_emoji("souls")
        souls = player_data.get("net_worth")
        description = f"**[ {hero_name} ]** {souls_emoji}{formatting.format_thousands(souls)} Souls"

        # Building embed
        embed = discord.Embed(
            title=f"{api.get_match_type(last_match.get("game_mode"), last_match.get("match_mode"))} ({outcome}) - {minutes}:{seconds:02d}",
            description=description,
            colour=colour
        )
        embed.set_thumbnail(url=hero_card)
        embed.add_field(name="Kills", value=f"`{formatting.pad_string(player_data.get("kills"))}`", inline=True)
        embed.add_field(name="Deaths", value=f"`{formatting.pad_string(player_data.get("deaths"))}`", inline=True)
        embed.add_field(name="Assists", value=f"`{formatting.pad_string(player_data.get("assists"))}`", inline=True)

        embed.add_field(name="Player Dmg", value=f"`{formatting.pad_string(
            f'{player_data.get("player_damage"):,}'
        )}`", inline=True)
        embed.add_field(name="Obj. Dmg", value=f"`{formatting.pad_string(
            f'{player_data.get("boss_damage"):,}'
        )}`", inline=True)
        embed.add_field(name="Healing", value=f"`{formatting.pad_string(
            f'{player_data.get("player_healing"):,}'
        )}`", inline=True)

        embed.add_field(name="Items", value=f"{" ".join(item_emoji_list)}", inline=False)

        # Footer text if MVP rank exists
        if mvp_rank is not None and mvp_image is not None:
            embed.set_footer(
                text=f"[ {mvp_title} ]",
                icon_url=f"attachment://{mvp_image_name}"
            )

            await interaction.followup.send(embed=embed, file=mvp_image)
        else:
            await interaction.followup.send(embed=embed)
    elif steam_id is None:
        response_message = 'You are not linked to a Steam account. Please link your Steam ID using `/link [steam_id]`.'
        await interaction.followup.send(response_message, ephemeral=True)
    elif len(match_history) == 0:
        response_message = 'Your account does not have a visible match history.'
        await interaction.followup.send(response_message, ephemeral=True)

    # await interaction.followup.send(response_message,embed=embed)

@app_commands.command(name="hero", description="Returns an overview of a specified hero's statistics.")
async def hero(interaction: discord.Interaction, name: str, public: bool = False):
    await interaction.response.defer(ephemeral=not public)

    steam_id = await get_user(interaction.user.id)

    match_history = (await api.make_request(f"/v1/players/{create_steam_id3(steam_id)}/match-history"))

    if steam_id is not None and len(match_history) != 0:
        hero_info = await api.make_request(f"/v1/assets/heroes/by-name/{name}")

        # Check valid hero name
        if hero_info is None or hero_info.get("status") == 404:
            response_message = f'Invalid hero name. Please try again.'
            await interaction.followup.send(response_message, ephemeral=True)
        else:
            # Retreive hero info
            hero_id = hero_info.get("id")
            hero_name = hero_info.get("name")
            hero_cards = {
                "normal": hero_info.get("images").get("icon_hero_card"),
                "critical": hero_info.get("images").get("hero_card_critical"),
                "gloat": hero_info.get("images").get("hero_card_gloat")
            }
            hero_card = hero_cards.get("normal")

            # Get hero stats from user
            hero_dict = await api.make_request("/v1/players/hero-stats",
                                         parameters={
                                            "account_ids": steam_id,
                                            "hero_ids": hero_id
                                         }
                                        )
            # If hero has no stats
            if len(hero_dict) == 0:
                response_message = 'No match history for the specified hero.'
                await interaction.followup.send(response_message, ephemeral=True)
            else:
                hero_data = hero_dict[0]

                # Create embed color from hero ui color
                rgb = hero_info.get("colors").get("ui")
                hero_color = discord.Color.from_rgb(rgb[0], rgb[1], rgb[2])

                # Creating embed description
                souls_emoji = await formatting.get_emoji("souls")
                description = f"**[ {hero_name} ]** {souls_emoji}{hero_data.get("networth_per_min"):,.0f} Souls/min"

                # Building embed
                embed = discord.Embed(
                    title=f'Hero Stats',
                    description=description,
                    colour=hero_color
                )

                embed.add_field(name="__Career Stats__", value="Statistics averaged over the span of your\ncareer with the character.", inline=False)

                embed.set_thumbnail(url=hero_card)


                embed.add_field(name="Matches", value=f"`{formatting.pad_string(
                    f'{hero_data.get("matches_played"):,}'
                )}`", inline=True)

                # embed.add_field(name="Wins", value=f"`{formatting.pad_string(
                #     f'{hero_data.get("wins"):,}'
                # )}`", inline=True)
                # embed.add_field(name="Losses", value=f"`{formatting.pad_string(
                #     f'{(hero_data.get("matches_played") - hero_data.get("wins")):,}'
                # )}`", inline=True)

                embed.add_field(name="Win Rate", value=f"`{formatting.pad_string(
                    f'{((hero_data.get("wins") / hero_data.get("matches_played")) * 100):.1f}%'
                )}`", inline=True)

                embed.add_field(name="Time Played", value=f"`{formatting.pad_string(
                    f'{(hero_data.get("time_played") / 3600):.0f} hrs'
                )}`", inline=True)

                embed.add_field(name="__Average Stats__", value="Statistics averaged per match or minute.", inline=False)

                embed.add_field(name="Kills ", value=f"`{formatting.pad_string(
                    f'{(hero_data.get("kills") / hero_data.get("matches_played")):.0f}'
                )}`", inline=True)
                embed.add_field(name="Deaths", value=f"`{formatting.pad_string(
                    f'{(hero_data.get("deaths") / hero_data.get("matches_played")):.0f}'
                )}`", inline=True)
                embed.add_field(name="Assists", value=f"`{formatting.pad_string(
                    f'{(hero_data.get("assists") / hero_data.get("matches_played")):.0f}'
                )}`", inline=True)

                embed.add_field(name="Player Dmg", value=f"`{formatting.pad_string(
                    f'{hero_data.get("damage_per_min"):,.0f}/min'
                )}`", inline=True)
                embed.add_field(name="Obj. Dmg", value=f"`{formatting.pad_string(
                    f'{hero_data.get("obj_damage_per_min"):,.0f}/min'
                )}`", inline=True)
                embed.add_field(name="Accuracy", value=f"`{formatting.pad_string(
                    f'{(hero_data.get("accuracy") * 100):,.1f}%'
                )}`", inline=True)

                await interaction.followup.send(embed=embed)
    elif steam_id is None:
        response_message = 'You are not linked to a Steam account. Please link your Steam ID using `/link [steam_id]`.'
        await interaction.followup.send(response_message, ephemeral=True)
    elif len(match_history) == 0:
        response_message = 'Your account does not have a visible match history.'
        await interaction.followup.send(response_message, ephemeral=True)

bot.setup_hook = setup_hook

# Adds the command associated with the given function.
bot.tree.add_command(link)
bot.tree.add_command(stats)
bot.tree.add_command(hero)

bot.run(DISCORD_TOKEN)