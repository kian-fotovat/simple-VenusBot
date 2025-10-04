import asyncio
import logging
import os
from pathlib import Path

import discord
from discord import app_commands
from dotenv import load_dotenv

from embed_views.queue_view import QueueView
from embed_views.search_view import SearchView
from music_controller import MusicController

# set up logging
logging.basicConfig(
    level=logging.INFO,  # Set logging level
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(f"{Path(__file__).resolve().parent / 'bot_log.log'}", mode="w", encoding="utf-8"), logging.StreamHandler()],
)

# block discords logging
logging.getLogger("discord").setLevel(logging.WARNING)


class VenusBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

        # Load environment variables
        load_dotenv()
        self.token = os.getenv("DISCORD_TOKEN")

        self.musicControllers = {}

    # function to get the music controller for the specificied guild
    async def getGuildMusicController(self, guild: discord.Guild):
        if guild.id not in self.musicControllers:
            self.musicControllers[guild.id] = MusicController(client=self, guild=guild)
        return self.musicControllers[guild.id]

    # function to pop the music controller for the specificied guild
    async def popGuildMusicController(self, guild: discord.Guild):
        if guild.id in self.musicControllers:
            self.musicControllers.pop(guild.id)

    async def on_ready(self):
        logging.info(f"{self.user} is now running.")
        await bot.tree.sync()
        logging.info("commands synced")

    async def on_connect(self):
        logging.info(f"{self.user} has connected.")

    async def start_bot(self):
        await self.start(self.token)


bot = VenusBot()


# event to disconnect or reconnect the bot from a voice channel based on number of members
@bot.event
async def on_voice_state_update(member, before, after):
    # make sure the bot itself doesn't trigger the event
    if member == bot.user:
        return

    # grab the musicController
    musicController = await bot.getGuildMusicController(member.guild)
    # grab the voice and text channel
    voiceChannel, textChannel = musicController.getVideoAndTextChannel()
    # check if bot is set to a channel
    if not voiceChannel or not textChannel:
        return

    # When a user joins a voice channel
    if before.channel is None and after.channel is not None:
        # if there is 1 member after joining, and the connected channel is the same as the /247 bot channel
        if len(after.channel.members) == 1 and after.channel == voiceChannel:
            await musicController.two_four_seven(voiceChannel, textChannel)

    # When a user leaves a voice channel
    elif before.channel is not None and after.channel is None:
        # if there is only the bot after leaving, and the connected channel is the same as the /247 bot channel
        if len(before.channel.members) == 1 and before.channel == voiceChannel:
            await musicController.softDisconnect()

    # When a user switches voice channels
    elif before.channel != after.channel:
        # if there is only the bot after leaving, and the connected channel is the same as the /247 bot channel
        if len(before.channel.members) == 1 and before.channel == voiceChannel:
            await musicController.softDisconnect()

        # if there is only 1 member at the after channel, and the connected channel is the same as the /247 bot channel
        if len(after.channel.members) == 1 and after.channel == voiceChannel:
            await musicController.two_four_seven(voiceChannel, textChannel)


@bot.tree.command(name="play", description="Play a Youtube, Spotify, or Soundcloud Song")
async def play(interaction: discord.Interaction, query: str):
    logging.info(f"{interaction.user.name} has activated /play")

    # grab the music controller for designated guild
    musicController = await bot.getGuildMusicController(guild=interaction.guild)
    # check if bot is connected to a voice channel
    if not musicController.isConnectedToVC():
        # check if user is in a voice channel
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("You or the Bot must be in a voice channel to use this command.")
            return
        else:
            await musicController.two_four_seven(interaction.user.voice.channel, interaction.channel)

    # send initial response
    await interaction.response.send_message("Searching For Song...", delete_after=5)

    # send the query to determine where the song comes from
    await musicController.determineSongSource(interaction.user, query)

    logging.debug(f"/play from {interaction.user.name} has ended")
    return


@bot.tree.command(name="247", description="Enables 24/7 Mode.")
async def two_four_seven(interaction: discord.Interaction, channel: discord.VoiceChannel):
    logging.info(f"{interaction.user.name} has activated /247")

    # grab the music controller for designated guild
    musicController = await bot.getGuildMusicController(guild=interaction.guild)
    # activate the /247 function
    response = await musicController.two_four_seven(channel, interaction.channel)
    if response:
        await interaction.response.send_message(f"Bot is currently in {response.channel.name}")
    else:
        await interaction.response.send_message(f"Enabling 24/7 Mode in {channel.name}")
    logging.debug(f"/247 from {interaction.user.name} has ended")
    return


@bot.tree.command(name="pause", description="Pause the current song. Will resume the song if already paused.")
async def pause(interaction: discord.Interaction):
    logging.info(f"{interaction.user.name} has activated /pause")

    # grab the music controller for designated guild
    musicController = await bot.getGuildMusicController(guild=interaction.guild)
    # call the /pause function
    response = await musicController.pauseSong()
    if response:
        await interaction.response.send_message("Pausing the song.")
    else:
        await interaction.response.send_message("Resuming Playback.")
    logging.debug(f"/pause from {interaction.user.name} has ended")
    return


@bot.tree.command(name="resume", description="Resume playback")
async def resume(interaction: discord.Interaction):
    logging.info(f"{interaction.user.name} has activated /resume")

    # grab the music controller for designated guild
    musicController = await bot.getGuildMusicController(guild=interaction.guild)
    # call the /resume function
    await musicController.resumeSong()
    await interaction.response.send_message("Resuming Playback.")
    logging.debug(f"/resume from {interaction.user.name} has ended")
    return


@bot.tree.command(name="shuffle", description="Shuffles the queue.")
async def shuffle(interaction: discord.Interaction):
    logging.info(f"{interaction.user.name} has activated /shuffle")

    # grab the music controller for designated guild
    musicController = await bot.getGuildMusicController(guild=interaction.guild)
    # call the /shuffle function
    await musicController.shuffleQueue()
    await interaction.response.send_message("Queue has been shuffled.")
    logging.debug(f"/shuffle from {interaction.user.name} has ended")
    return


@bot.tree.command(name="stop", description="Stop playback and clear queue")
async def stop(interaction: discord.Interaction):
    logging.info(f"{interaction.user.name} has activated /stop")

    # grab the music controller for designated guild
    musicController = await bot.getGuildMusicController(guild=interaction.guild)
    await interaction.response.send_message("Stopping playback and clearing queue.")
    # call the /stop function
    await musicController.stopAllSongs()

    logging.debug(f"/stop from {interaction.user.name} has ended")
    return


@bot.tree.command(name="dc", description="Kicks the bot from the voice channel, and turns off 24/7.")
async def kick(interaction: discord.Interaction):
    logging.info(f"{interaction.user.name} has activated /dc")

    # grab the music controller for designated guild
    musicController = await bot.getGuildMusicController(guild=interaction.guild)
    # call the /dc function
    await musicController.hardDisconnect()
    # pop the music Controller
    await bot.popGuildMusicController(guild=interaction.guild)
    await interaction.response.send_message("Bot has been disconnected from the voice channel, and 24/7 has been disabled.")
    logging.debug(f"/dc from {interaction.user.name} has ended")
    return


@bot.tree.command(name="skip", description="Skip the current song")
async def skip(interaction: discord.Interaction):
    logging.info(f"{interaction.user.name} has activated /skip")

    # grab the music controller for designated guild
    musicController = await bot.getGuildMusicController(guild=interaction.guild)
    await interaction.response.send_message("Skipping song.")
    # call the /skip function
    await musicController.skipSong()
    logging.debug(f"/skip from {interaction.user.name} has ended")
    return


@bot.tree.command(name="loop", description="Loops the currently playing song.")
async def loop(interaction: discord.Interaction):
    logging.info(f"{interaction.user.name} has activated /loop")

    # grab the music controller for designated guild
    musicController = await bot.getGuildMusicController(guild=interaction.guild)
    # call the /loop function
    response = await musicController.setLooping()
    if response:
        await interaction.response.send_message("Looping Enabled.")
    else:
        await interaction.response.send_message("Looping Disabled.")
    logging.debug(f"/loop from {interaction.user.name} has ended")
    return


@bot.tree.command(name="queue", description="Display the queue")
async def queue(interaction: discord.Interaction):
    logging.info(f"{interaction.user.name} has activated /queue")

    # grab the music controller for designated guild
    musicController = await bot.getGuildMusicController(guild=interaction.guild)
    # get songQueue from the music controller
    queue = musicController.getSongQueue()
    # if no songs in queue
    if len(queue) <= 1:
        embed = discord.Embed(
            title="Queue",
            description="No songs in the queue.",
            color=0xA600FF,
        )
        embed.set_thumbnail(url=bot.user.avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # grab the QueueView Class
    view = QueueView(queue, bot, interaction.user)
    # send the discord embed for the queue
    await view.send_page(interaction, first_response=True)
    logging.debug(f"/queue from {interaction.user.name} has ended")
    return


@bot.tree.command(name="search", description="Search for the top 10 results.")
async def search(interaction: discord.Interaction, query: str):
    logging.info(f"{interaction.user.name} has activated /search")

    # send the initial discord message
    await interaction.response.send_message(f"Searching Youtube: {query}", delete_after=3)
    # grab the music controller for designated guild
    musicController = await bot.getGuildMusicController(guild=interaction.guild)
    # search for the query
    result = await musicController.searchSongs(query)
    if not result:
        await interaction.channel.send("Failed to search youtube.")
        return
    # grab the SearchView Class
    view = SearchView(result, musicController, bot)
    # send the discord embed for the search
    await view.send_page(interaction)
    logging.debug(f"/search from {interaction.user.name} has ended")
    return


@bot.tree.command(name="volume", description="Set the volume of the bot.")
@app_commands.describe(volume="A number between 0 and 200, 100 is default.")
async def volume(interaction: discord.Interaction, volume: app_commands.Range[int, 0, 200]):
    logging.info(f"{interaction.user.name} has activated /volume")

    # grab the music controller for designated guild
    musicController = await bot.getGuildMusicController(guild=interaction.guild)

    # call the /volume function
    await musicController.setVolume(volume)
    await interaction.response.send_message(f"Volume has been set to {volume}%")
    logging.debug(f"/volume from {interaction.user.name} has ended")
    return


@bot.tree.command(name="help", description="List of all commands.")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="All Commands",
        color=0xA600FF,
    )
    embed.add_field(name="/Play", value="Enter a URL or the name of the song, will play or queue the song. Youtube, Spotify, and SoundCloud only.", inline=True)
    embed.add_field(name="/247", value="Enables 24/7 Mode in a channel.", inline=False)
    embed.add_field(name="/DC", value="Kicks the bot from the voice channel, and turns off 24/7.", inline=False)
    embed.add_field(name="/Shuffle", value="Shuffles the queue.", inline=False)
    embed.add_field(name="/Loop", value="Enables/Disables Looping on the current song.", inline=False)
    embed.add_field(name="/Stop", value="Stops playing the current song, and removes all songs from queue.", inline=False)
    embed.add_field(name="/Skip", value="Skips the current song.", inline=False)
    embed.add_field(name="/Pause", value="Pauses the current song.", inline=False)
    embed.add_field(name="/Resume", value="Resumes the current song from where it left off.", inline=False)
    embed.add_field(name="/Queue", value="Shows the queue of songs, can move or remove songs from queue here.", inline=False)
    embed.add_field(name="/Search", value="Searches for top 10 results of a song. Use this in case you can't find what you want.", inline=False)
    embed.add_field(name="/Volume", value="Sets the volume of the bot, between 0 and 200. 100 is the default.", inline=False)
    embed.set_thumbnail(url=bot.user.avatar.url)
    await interaction.response.send_message(embed=embed)


if __name__ == "__main__":
    asyncio.run(bot.start_bot())
