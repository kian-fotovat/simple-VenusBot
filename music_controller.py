import asyncio
import logging
import random
import re
import time
from typing import Tuple

import discord

from embed_views.music_buttons import MusicButtons
from scripts.spotify import SpotifyController
from scripts.ytDLP import VideoSearcher, getSongExpiration


class Song:
    def __init__(self, title: str, url: str, link: str, thumbnail: str, duration: int, user: discord.User):
        self.title = title
        self.url = url
        self.link = link
        self.thumbnail = thumbnail
        self.duration = duration
        self.user = user


class MusicController:
    # Constructor
    def __init__(self, client: discord.Client, guild: discord.Guild):
        logging.info(f"Created Music Controller for: {guild}")
        self.client = client
        self.guild = guild
        self.spotify = SpotifyController()
        # self.loop = asyncio.get_running_loop() # apparently not necessary, use self.client.loop
        self.voiceChannel = None
        self.textChannel = None
        self.songQueue = []
        self.isLooping = False
        self.start_time = None
        self.pause_start = None
        self.pause_duration = 0
        self.volume = 1.0

    # function to check if the bot is currently connected to a voice channel
    def isConnectedToVC(self):
        voice_client = discord.utils.get(self.client.voice_clients, guild=self.guild)
        if voice_client and voice_client.is_connected():
            logging.debug(f"{self.guild.name} Music Controller is connected to a voice channel.")
            return True
        else:
            logging.debug(f"{self.guild.name} Music Controller is not connected to any voice channel.")
            return False

    # function to get the voice and text channel
    def getVideoAndTextChannel(self) -> Tuple[discord.VoiceChannel, discord.TextChannel]:
        return self.voiceChannel, self.textChannel

    # function to get the song queue
    def getSongQueue(self) -> list:
        return self.songQueue

    # function to set the volume
    async def setVolume(self, volume: int) -> float:
        logging.debug(f"Setting volume to {volume}")
        self.volume = volume / 100
        # Check if a song is currently playing and adjust the volume
        voice_client = discord.utils.get(self.client.voice_clients, guild=self.guild)
        if voice_client and voice_client.source:
            voice_client.source.volume = self.volume
        return self.volume

    # function to set looping
    async def setLooping(self) -> bool:
        logging.debug("Starting /loop function")
        self.isLooping = not self.isLooping
        return self.isLooping

    # function to skip current song
    async def shuffleQueue(self):
        logging.debug("Starting /shuffle function")
        if self.isConnectedToVC():
            if len(self.songQueue) <= 1:
                return
            # Preserve the first song
            first_song = self.songQueue[0]
            rest = self.songQueue[1:]
            # Shuffle the remaining songs
            random.shuffle(rest)
            # Reassign the shuffled list back to the queue
            self.songQueue[:] = [first_song] + rest
        return

    async def searchSongs(self, query: str):
        logging.debug("Starting /search function")
        # get the video searcher class
        searcher = VideoSearcher()
        try:
            result = await searcher.getSearchResults(query)
        except Exception as e:
            logging.error(e)
            await self.textChannel.send(f"Unable to search for songs: {e}")
            return
        # check if result came back successfully
        if not result:
            await self.textChannel.send("Unable to search for songs: unknown error")
            return
        return result

    # function to skip current song
    async def skipSong(self, message: discord.Message = None):
        logging.debug("Starting /skip function")
        if self.isConnectedToVC():
            voice_client = discord.utils.get(self.client.voice_clients, guild=self.guild)
            voice_client.stop()
            return

    # function to pause current song
    async def pauseSong(self):
        logging.debug("Starting /pause function")
        if self.isConnectedToVC():
            voice_client = discord.utils.get(self.client.voice_clients, guild=self.guild)
            if not voice_client.is_paused():
                voice_client.pause()
                self.pause_start = int(time.time())
                return True
            else:
                voice_client.resume()
                self.pause_duration += int(time.time()) - self.pause_start
                return False

    # function to resume current song
    async def resumeSong(self):
        logging.debug("Starting /resume function")
        if self.isConnectedToVC():
            voice_client = discord.utils.get(self.client.voice_clients, guild=self.guild)
            if voice_client.is_paused():
                voice_client.resume()
                self.pause_duration += int(time.time()) - self.pause_start
        return

    # function to stop all songs
    async def stopAllSongs(self, message: discord.Message = None):
        logging.debug("Starting /stop function")
        if self.isConnectedToVC():
            voice_client = discord.utils.get(self.client.voice_clients, guild=self.guild)
            self.songQueue = []
            self.isLooping = False
            voice_client.stop()
            return

    # function to soft disconnect the bot. This is used when a bot is the only one left in a voice channel and should leave, being able to reconnect later
    async def softDisconnect(self):
        if self.isConnectedToVC() is True:
            voice_client = discord.utils.get(self.client.voice_clients, guild=self.guild)
            self.songQueue = []
            self.isLooping = False
            await voice_client.disconnect(force=False)
            logging.debug(f"{self.guild.name} Music Controller has been soft disconnected.")

    # function to hard disconnect the bot.
    async def hardDisconnect(self):
        if self.isConnectedToVC() is True:
            voice_client = discord.utils.get(self.client.voice_clients, guild=self.guild)
            self.songQueue = []
            self.isLooping = False
            await voice_client.disconnect(force=True)
            logging.debug(f"{self.guild.name} Music Controller has been hard disconnected.")

    # function to join the channel
    async def two_four_seven(self, voiceChannel: discord.VoiceChannel, textChannel: discord.TextChannel) -> discord.VoiceClient:
        logging.debug("Starting /247 function")
        if self.isConnectedToVC() is not True:
            logging.debug("Bot is not in channel, connecting...")
            await voiceChannel.connect()
            logging.info(f"Bot succesfully connected to {voiceChannel.name}")
            self.voiceChannel = voiceChannel
            self.textChannel = textChannel
            return None
        else:
            voice_client = discord.utils.get(self.client.voice_clients, guild=self.guild)
            logging.debug(f"Bot is already in channel: {voice_client.channel.name}")
            return voice_client

    async def determineSongSource(self, user: discord.User, query: str):
        logging.debug("In Determine Song Source")
        query_lower = query.lower()

        # Regex patterns
        youtube_pattern = re.compile(r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/")
        youtube_playlist_pattern = re.compile(r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/playlist\?list=[\w-]+")
        spotify_pattern = re.compile(r"(https?://)?(open\.)?spotify\.com/")
        spotify_playlist_pattern = re.compile(r"(https?://)?(open\.)?spotify\.com/(playlist|album)/[a-zA-Z0-9]+")
        soundcloud_pattern = re.compile(r"(https?://)?(www\.)?soundcloud\.com/")
        soundcloud_playlist_pattern = re.compile(r"^(https?://)?(www\.)?soundcloud\.com/[^/]+/sets/[^/]+/?")

        # Determine source
        if youtube_pattern.search(query_lower):
            logging.debug("Detected YouTube link")
            if youtube_playlist_pattern.search(query_lower):
                logging.debug("Detected YouTube playlist")
                return await self.handleYoutubePlaylist(user, query)
            return await self.handleYoutubeLink(user, query)
        elif spotify_pattern.search(query_lower):
            logging.debug("Detected Spotify link")
            if spotify_playlist_pattern.search(query_lower):
                logging.debug("Detected spotify playlist/album")
                return await self.handleSpotifyPlaylist(user, query)
            return await self.handleSpotifyLink(user, query)
        elif soundcloud_pattern.search(query_lower):
            logging.debug("Detected SoundCloud link")
            if soundcloud_playlist_pattern.search(query_lower):
                logging.debug("Detected SoundCloud playlist")
                return await self.handleSoundCloudPlaylist(user, query)
            return await self.handleSoundCloudLink(user, query)
        else:
            logging.debug("Detected search query - assuming YouTube search")
            return await self.handleYoutubeSearch(user, query)

    async def handleYoutubeLink(self, user, url):
        logging.debug("In handleYoutubeLink")
        # get the song info from the youtube link
        searcher = VideoSearcher()
        try:
            result = await searcher.getVideoInfoFromURL(url)
        except Exception as e:
            logging.error(e)
            await self.textChannel.send(f"Unable to add song: {e}")
            return
        # check if result came back successfully
        if not result:
            await self.textChannel.send("Unable to find song.")
            return
        # create a song object
        youtubeSong = Song(result["title"], url, result["link"], result["thumbnail"], result["duration"], user)
        # queue the song
        await self.queueSong(youtubeSong)
        return

    async def handleYoutubePlaylist(self, user, url):
        logging.debug("In handleYoutubePlaylist")
        # get the playlist info from the youtube link
        searcher = VideoSearcher()
        result = await searcher.getPlaylistInfo(url)
        # check if result came back successfully
        if not result:
            await self.textChannel.send("Unable to find playlist.")
            return
        # get the playlist name and the number of songs
        metadata = result.pop(0)
        thumbnail = metadata.get("thumbnail") or self.client.user.avatar.url
        # send the "Adding Playlist" discord embed
        embed = discord.Embed(
            title="Adding Playlist:",
            color=0xA600FF,
        )
        embed.set_thumbnail(url=thumbnail)
        embed.add_field(name="Playlist Name", value=metadata["playlist_name"], inline=False)
        embed.add_field(name="# of Songs", value=metadata["song_count"], inline=False)
        await self.textChannel.send(embed=embed)
        for song in result:
            logging.debug(f"Searching for {song['url']}")
            try:
                # grab the video info for each song in the playlist
                songInfo = await searcher.getVideoInfoFromURL(song["url"])
            except Exception as e:
                logging.error(e)
                await self.textChannel.send(f"Unable to add song: {e}")
                continue
            # create a song object and append it to the playlist
            youtubeSong = Song(songInfo["title"], song["url"], songInfo["link"], songInfo["thumbnail"], songInfo["duration"], user)
            # queue the song
            await self.queueSong(youtubeSong)
        return

    async def handleSpotifyLink(self, user, url):
        logging.debug("In handleSpotifyLink")
        # get the name and artist of song from spotify API
        spotifySongInfo = await self.spotify.getSpotifySongInfo(url)
        query = f"{spotifySongInfo['title']} by {spotifySongInfo['artist']}"
        logging.debug(f"searching for spotify song: {query}")
        # get the song info from the youtube search query
        searcher = VideoSearcher()
        try:
            result = await searcher.getVideoInfoFromQuery(query)
        except Exception as e:
            logging.error(e)
            await self.textChannel.send(f"Unable to add song: {e}")
            return
        # check if result came back successfully
        if not result:
            await self.textChannel.send("Unable to find song.")
            return
        # create a song object
        youtubeSong = Song(result["title"], result["url"], result["link"], result["thumbnail"], result["duration"], user)
        # queue the song
        await self.queueSong(youtubeSong)
        return

    async def handleSpotifyPlaylist(self, user, playlist):
        logging.debug("In handleSpotifyPlaylist")
        # get the playlist info from spotify API
        result = await self.spotify.getSpotifyPlaylistInfo(playlist)
        # check if result came back successfully
        if not result:
            await self.textChannel.send("Unable to find spotify playlist/album.")
            return
        # get the playlist name, number of songs, and thumbnail
        playlist_info = result.pop(0)
        thumbnail = playlist_info.get("thumbnail") or self.client.user.avatar.url
        # send the "Adding Playlist" discord embed
        embed = discord.Embed(
            title="Adding Playlist:",
            color=0xA600FF,
        )
        embed.set_thumbnail(url=thumbnail)
        embed.add_field(name="Playlist Name", value=playlist_info["title"], inline=False)
        embed.add_field(name="# of Songs", value=len(result), inline=False)
        await self.textChannel.send(embed=embed)
        searcher = VideoSearcher()
        for song in result:
            query = f"{song['title']} by {song['artist']}"
            logging.debug(f"Searching for {query}")
            try:
                # grab the video info for each song in the playlist
                songInfo = await searcher.getVideoInfoFromQuery(query)
            except Exception as e:
                logging.error(e)
                await self.textChannel.send(f"Unable to add song: {e}")
                continue
            # create a song object
            youtubeSong = Song(songInfo["title"], songInfo["url"], songInfo["link"], songInfo["thumbnail"], songInfo["duration"], user)
            # queue the song
            await self.queueSong(youtubeSong)
        return

    async def handleSoundCloudLink(self, user, url):
        logging.debug("In handleSoundCloudLink")
        # get the song info from the soundcloud link
        searcher = VideoSearcher()
        try:
            result = await searcher.getVideoInfoFromURL(url)
        except Exception as e:
            logging.error(e)
            await self.textChannel.send(f"Unable to add song: {e}")
            return
        # check if result came back successfully
        if not result:
            await self.textChannel.send("Unable to find song.")
            return
        # create a song object
        soundcloudSong = Song(result["title"], url, result["link"], result["thumbnail"], result["duration"], user)
        # queue the song
        await self.queueSong(soundcloudSong)
        return

    async def handleSoundCloudPlaylist(self, user, url):
        logging.debug("In handleSoundCloudPlaylist")
        # get the playlist info from the soundcloud link
        searcher = VideoSearcher()
        result = await searcher.getPlaylistInfo(url)
        # check if result came back successfully
        if not result:
            await self.textChannel.send("Unable to find playlist.")
            return
        # get the playlist name and the number of songs
        metadata = result.pop(0)
        thumbnail = metadata.get("thumbnail") or self.client.user.avatar.url
        # send the "Adding Playlist" discord embed
        embed = discord.Embed(
            title="Adding Playlist:",
            color=0xA600FF,
        )
        embed.set_thumbnail(url=thumbnail)
        embed.add_field(name="Playlist Name", value=metadata["playlist_name"], inline=False)
        embed.add_field(name="# of Songs", value=metadata["song_count"], inline=False)
        await self.textChannel.send(embed=embed)
        for song in result:
            logging.debug(f"Searching for {song['url']}")
            try:
                # grab the video info for each song in the playlist
                songInfo = await searcher.getVideoInfoFromURL(song["url"])
            except Exception as e:
                logging.error(e)
                await self.textChannel.send(f"Unable to add song: {e}")
                continue
            # create a song object and append it to the playlist
            soundcloudSong = Song(songInfo["title"], song["url"], songInfo["link"], songInfo["thumbnail"], songInfo["duration"], user)
            # queue the song
            await self.queueSong(soundcloudSong)
        return

    async def handleYoutubeSearch(self, user, query):
        logging.debug("In handleYoutubeSearch")
        # get the song info from the youtube search query
        searcher = VideoSearcher()
        try:
            result = await searcher.getVideoInfoFromQuery(query)
        except Exception as e:
            logging.error(e)
            await self.textChannel.send(f"Unable to add song: {e}")
            return
        # check if result came back successfully
        if not result:
            await self.textChannel.send("Unable to find song.")
            return
        # create a song object
        youtubeSong = Song(result["title"], result["url"], result["link"], result["thumbnail"], result["duration"], user)
        # queue the song
        await self.queueSong(youtubeSong)
        return

    async def queueSong(self, song: Song):
        logging.debug("In queueSong")
        # check if song should play right away or go into the queue
        if not self.songQueue:
            logging.debug("Queue is empty, playing song right away.")
            self.songQueue.append(song)
            print("songQueue: ", self.songQueue)
            await self.playSong()
            return
        else:
            logging.debug("Adding song to queue.")
            self.songQueue.append(song)
            print("songQueue: ", self.songQueue)
            # send the "Added to Queue" discord embed
            embed = discord.Embed(
                title="Added to Queue:",
                description=song.title,
                color=0xA600FF,
            )
            embed.set_thumbnail(url=song.thumbnail)
            await self.textChannel.send(embed=embed)
            return

    async def queuePlaylist(self, playlist: list):
        logging.debug("In queuePlaylist")
        # pop the thumbnail from the playlist
        thumbnail = playlist.pop(0)
        # check if playlist should play right away or go into the queue
        if not self.songQueue:
            logging.debug("Queue is empty, playing playlist right away.")
            for song in playlist:
                self.songQueue.append(song)
            print("songQueue: ", self.songQueue)
            await self.playSong()
        else:
            logging.debug("Adding playlist to queue.")
            for song in playlist:
                self.songQueue.append(song)
            print("songQueue: ", self.songQueue)

        # send the "Added to Queue" discord embed
        embed = discord.Embed(
            title="Playlist Added to Queue:",
            color=0xA600FF,
        )
        embed.set_thumbnail(url=thumbnail)
        for i, song in enumerate(playlist, start=1):
            embed.add_field(name=f"{i}", value=song.title, inline=False)
        await self.textChannel.send(embed=embed)
        return

    async def playSong(self):
        logging.debug("In playSong.")

        # check to make sure there is a song in queue
        if not self.songQueue:
            await self.textChannel.send("No more songs to play.")
            self.start_time = None
            self.pause_duration = 0
            self.pause_start = None
            return

        ffmpeg_options = {"before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", "options": "-vn"}

        # get the next song to play
        song = self.songQueue[0]

        if getSongExpiration(song.link) <= int(time.time()):
            logging.debug("Stream URL is expired. Fetching new one")
            # get the song info from the link
            searcher = VideoSearcher()
            try:
                result = await searcher.getVideoInfoFromURL(song.url)
            except Exception as e:
                logging.error(e)
                await self.textChannel.send(f"Unable to add song: {e}")
                return
            # update the current songs stream link
            song.link = result["link"]

        # create the discord player for current song
        source = discord.FFmpegPCMAudio(song.link, **ffmpeg_options)
        player = discord.PCMVolumeTransformer(source, volume=self.volume)

        # function to call after a song is done playing
        def after_playing(error):
            if error:
                logging.error(f"Error during playback: {error}")
            else:
                if self.isLooping:
                    logging.debug("Song finished, replaying previous song.")
                else:
                    logging.debug("Song finished, popping from queue and checking next")
                    if self.songQueue:
                        self.songQueue.pop(0)
                fut = asyncio.run_coroutine_threadsafe(self.playSong(), self.client.loop)
                fut.add_done_callback(lambda f: f.exception())

        # get the voice client and play the song
        voice_client = discord.utils.get(self.client.voice_clients, guild=self.guild)
        voice_client.play(player, after=after_playing)

        # start the duration timer
        self.start_time = int(time.time())
        self.pause_duration = 0
        self.pause_start = None

        # send the "Now Playing" discord embed
        embed = discord.Embed(
            title="Now Playing:",
            description=song.title,
            color=0xA600FF,
        )
        embed.set_thumbnail(url=song.thumbnail)
        await self.textChannel.send(embed=embed, view=MusicButtons(client=self.client))
