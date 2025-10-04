# 🎶 Venus Bot - A Voice Activated 24/7 Discord Music Bot

Venus Bot is a simple, yet powerful and customizable Discord music bot built with `discord.py`, capable of playing songs or playlists from YouTube, Spotify and SoundCloud. No fancy bullshit or e-kitten fluff, just a bot that plays music. Expect some minor bugs, I literally ripped everything I didn't want out, tested it for 10 minutes, and pushed it here.

Created by [VenusMods](https://github.com/VenusMods) and slimmed by kian :)

---

## ✨ Features

- 🎧 **Play Songs/Playlists** from YouTube, Spotify, or SoundCloud
- 📜 **Smart Queue System** with paging, reordering, shuffle, and prioritization
- 🎶 **Search and Select** songs directly from Discord using dropdowns
- 🛠️ **Smart Connect** — allows the bot to join the channel when you join, or leaves when you leave
---

## 🚀 Getting Started

-Note: If all of the features of the bot are working besides actually playing music, just update your yt-dlp package.

> **Before You Start:**
>
> - ✅ You must have **[FFmpeg](https://ffmpeg.org/download.html)** installed and available in your system’s `PATH`
> - ✅ You must use **Python 3.11** and create a virtual environment in the root directory
> - ✅ You need to configure the `.env` file before running the bot

---

### 🔧 Step-by-Step Setup

```bash
# Clone the repository
git clone https://github.com/VenusMods/VenusBot.git
cd VenusBot

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```
### 🧪 .env Setup
```
DISCORD_TOKEN='YOUR_BOT_TOKEN_HERE'
SPOTIFY_CLIENT_ID='YOUR_SPOTIFY_CLIENT_ID'
SPOTIFY_CLIENT_SECRET='YOUR_SPOTIFY_CLIENT_SECRET'
SPOTIFY_CLIENT_REFRESH_TOKEN='YOUR_SPOTIFY_REFRESH_TOKEN'
OWNER=000000000000000000
```
- Replace `YOUR_BOT_TOKEN_HERE` with your Discord Bot Token
- Replace Spotify credentials with ones from the **[Spotify Developer Dashboard](https://developer.spotify.com/dashboard)**
- OWNER should be your Discord user ID.
> - To get it:
> - Go to Discord Settings → Advanced → Enable Developer Mode
> - Click your username → Click "Copy User ID"

### 🤖 Run the Bot
```bash
# in a virtual environment
python venusbot.py
```

---

### Smart Connect
- While the bot is in 24/7 mode, the bot will join the channel when you join, or it will leave when it is the last one left in the channel.
---

## ✨ Basic Command Usage and Examples
### /247
Connect the bot to a voice channel and set it to 24/7 mode. The bot will leave when it's the last one in the call, and it'll join when someone enters the call. all other commands that play music also activate 24/7 mode if the user is in a voice channel.

### /dc
Kicks the bot from the voice channel, and turns off 24/7.

### /play
Play a song/playlist from Youtube, Spotify, or SoundCloud. 
- Examples
```
/play Not Allowed by TV Girl 
```
```
/play https://www.youtube.com/watch?v=9wiEM0s4aCQ
```
```
/play https://open.spotify.com/album/6trNtQUgC8cgbWcqoMYkOR
```
```
/play https://soundcloud.com/uiceheidd/scared-of-love?in=jason-the_god/sets/juice-wrld-playlist&utm_source=clipboard&utm_medium=text&utm_campaign=social_sharing
```

### /loop
Enables/Disables Looping on the current song.

### /skip
Skips the current song.

### /stop
Stops playing the current song, and removes all songs from queue.

### /pause
Pauses the current song. If already paused, will resume the song.

### /resume
Resumes the current song from where it left off.

### /queue
Shows the queue of songs, can move or remove songs from queue here.

![queue](https://github.com/user-attachments/assets/34a33851-8bdc-486d-aca7-82a7883f1974)

### /shuffle
Shuffles the queue.

### /search
Searches for top 10 results of a song. Use this in case you can't find what you want.

### /volume
Sets the volume of the bot, between 0 and 200. 100 is the default.
