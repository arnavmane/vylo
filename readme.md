# 🌙 Vylo Bot

**Vylo** is a modern, feature-rich, and aesthetic Discord bot built with `discord.py`. It features a modular architecture, an interactive setup dashboard, high-quality music playback, an advanced levelling system, and a powerful moderation suite—all wrapped in a sleek, premium design.

## ✨ Features

### 🛠️ Interactive Setup
- **Dashboard**: Run `.setup` to open a GUI dashboard.
- **Toggles**: Enable/Disable modules (Music, Fun, Moderation, Levels, etc.) with a click.
- **Configuration**: Set Log channels, toggle Welcome messages, and change the Prefix directly from the UI.

### 🎶 High-Quality Music
- **Core Commands**: `.play`, `.skip`, `.stop`, `.queue`, `.leave`.
- **Quality**: URL stream extraction via `yt-dlp` and playback via `FFmpeg`.
- **Aesthetics**: Beautiful "Now Playing" embeds and queue lists.

### 🛡️ Moderation & Logging
- **Actions**: `kick`, `ban`, `mute`, `warn`, `purge`, `nuke`.
- **Channel Mgmt**: `lock`, `unlock`, `slowmode`.
- **Logging**: Tracks member joins/leaves, message edits/deletes, and mod actions to a configured channel.

### 📈 Levelling & Ranks
- **XP Ecosystem**: Gain XP dynamically by chatting.
- **Track Progress**: Use `.rank` to check your beautifully formatted current rank.
- **Leaderboards**: Use `.leaderboard` to check the top contributors in your server.

### 🎮 Fun & Media
- **Reddit**: Fetch memes, cats, and dogs directly from Reddit.
- **Games**: Rock Paper Scissors, Coin Flip, Dice Roll, Guess the Number.
- **Utils**: Trivia, Quotes, Jokes, and more.

## 🚀 Installation

1.  **Clone the Repo**:
    ```bash
    git clone https://github.com/yourusername/vylo.git
    cd vylo
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Setup FFmpeg**:
    - Download `ffmpeg.exe` and place it in the root folder (for Music support).

4.  **Configure Environment**:
    - Ensure you have **Python 3.10+** installed.
    - Create a `.env` file in the root directory:
      ```env
      BOT_TOKEN=your_discord_bot_token_here
      ```

5.  **Run**:
    ```bash
    python main.py
    ```

## 🔮 Future Scope

- **Web Dashboard**: A React/Next.js frontend to manage bot settings online.
- **Ticket System**: Private support channels for users.
- **Auto-Moderation**: AI-powered anti-spam and toxicity filters.

*Built with ❤️ using Python & Discord.py :)*
