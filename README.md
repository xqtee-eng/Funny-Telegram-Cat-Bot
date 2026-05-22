# Funny Telegram Cat Bot

Funny Telegram Cat Bot is a Python Telegram bot for quick text effects and a small Telegram Mini App UI. It can generate random funny text, transform user text, send limited separate-message spam for private fun, and open a web interface directly from Telegram.

The project intentionally uses only the Python standard library for the bot side. No `pip install` is required.

## Features

- Telegram command menu with descriptions
- Random Ukrainian meme-style text generator
- Text effects: caps, lower, title, mock, reverse, shuffle, clap, emoji, vaporwave, zalgo
- Meme and roast templates
- Limited `/spam` command that sends separate messages
- Telegram Mini App from `mini_app/`
- One-command local startup on Windows through `start_all.ps1`
- One-command shutdown through `stop_all.ps1`
- Unit tests for bot parsing and text tools

## Project Structure

```text
.
├── bot.py                  # Telegram bot polling and command handling
├── text_tools.py           # Text effects and random text generation
├── mini_app/               # Telegram Mini App static frontend
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── start_all.ps1           # Starts Mini App server, tunnel, sync, and bot
├── stop_all.ps1            # Stops bot, Mini App server, and tunnel
├── sync_tunnel_url.py      # Updates .env and Telegram menu button with tunnel URL
├── configure_menu.py       # Updates Telegram commands/menu button
├── configure_profile.py    # Updates bot name/description/profile texts
├── test_bot.py
├── test_text_tools.py
├── .env.example
└── README.md
```

## Requirements

- Python 3.11+
- Windows PowerShell for the helper scripts
- OpenSSH client available as `ssh`
- Telegram bot token from [BotFather](https://t.me/BotFather)

The one-command local Mini App setup uses [localhost.run](https://localhost.run/) as a temporary HTTPS tunnel.

## Setup

Clone the repository:

```powershell
git clone https://github.com/xqtee-eng/Funny-Telegram-Cat-Bot.git
cd Funny-Telegram-Cat-Bot
```

Create `.env` from the example:

```powershell
copy .env.example .env
```

Open `.env` and put your BotFather token:

```env
TELEGRAM_BOT_TOKEN=your_real_token_from_botfather
TELEGRAM_WEB_APP_URL=https://your-public-https-site.example
```

For local Mini App testing, `TELEGRAM_WEB_APP_URL` can be left as a placeholder. `start_all.ps1` will replace it with the current `localhost.run` URL.

Do not commit `.env`. It is ignored by git.

## Quick Start

Start the bot and Mini App together:

```powershell
powershell -ExecutionPolicy Bypass -File .\start_all.ps1
```

What this script does:

- starts the Mini App static server at `http://127.0.0.1:8787`
- starts a temporary HTTPS tunnel through `localhost.run`
- waits until the tunnel returns HTTP 200
- writes the tunnel URL to `.env`
- updates the Telegram Mini App menu button
- starts `bot.py`

Keep this PowerShell window open while the bot is running.

If the Mini App opens but the send button does not deliver anything to the chat, open the bot chat and send:

```text
/app
```

Then press the Web App button that the bot sends in the chat. Telegram allows `sendData()` most reliably from that bot-provided Web App button. The bottom menu button is still useful for opening the interface, but some Telegram clients do not send data back from that launch mode.

## Stop Everything

Stop the bot, Mini App server, and tunnel:

```powershell
powershell -ExecutionPolicy Bypass -File .\stop_all.ps1
```

`Ctrl+C` stops only the bot if it is running in the current terminal. Use `stop_all.ps1` when you also want to stop the web server and tunnel.

## Manual Start

Use this mode if you want to debug each piece separately.

Start only the bot:

```powershell
python bot.py
```

Start only the Mini App local server:

```powershell
python -m http.server 8787 --directory mini_app
```

Start the HTTPS tunnel:

```powershell
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=localhostrun_known_hosts -o ServerAliveInterval=30 -R 80:127.0.0.1:8787 nokey@localhost.run
```

After the tunnel starts, update the Telegram menu button:

```powershell
python sync_tunnel_url.py
```

If you already have a working `localhost.run` URL and want to force Telegram to use exactly that URL:

```powershell
python sync_tunnel_url.py https://your-current-url.lhr.life
```

## Bot Commands

After startup, the bot registers its Telegram command menu. In Telegram, type `/` in the chat to see the command list.

| Command | Description |
| --- | --- |
| `/start` | Show command list |
| `/help` | Show command list |
| `/random [count]` | Generate random funny text |
| `/caps <text>` | Convert text to uppercase |
| `/lower <text>` | Convert text to lowercase |
| `/title <text>` | Capitalize each word |
| `/mock <text>` | Apply alternating mock case |
| `/reverse <text>` | Reverse text |
| `/shuffle <text>` | Shuffle words or letters |
| `/clap <text>` | Add claps between words |
| `/emoji <text>` | Add random emoji between words |
| `/vapor <text>` | Apply vaporwave style |
| `/zalgo <text>` | Add chaotic combining marks |
| `/meme <text>` | Create a meme-style template |
| `/roast <text>` | Create a light roast |
| `/spam <1-50> <text>` | Send text as separate messages |
| `/app` | Show Mini App open button |
| `/cancel` | Cancel a command waiting for text |

Text commands can be used directly:

```text
/reverse привіт
```

You can also send a command without text, for example `/reverse`, and then send the text in the next message. If you reply to an existing Telegram message with a command, the bot can use the replied message text.

If a user sends plain text without a command, the bot applies a random effect.

## Mini App

The Mini App is a static frontend inside `mini_app/`.

It uses the Telegram Web App API:

```js
Telegram.WebApp.sendData(...)
```

The frontend sends action data to the bot. The bot receives `web_app_data`, applies the selected effect, and sends the result back into the chat.

For sending generated text back to the chat, prefer opening the Mini App through `/app`. If a Telegram client opens the Mini App from the bottom menu but ignores the send button, this is a Telegram launch-mode limitation, not a bot crash.

For real public use, deploy `mini_app/` to a stable HTTPS host and set:

```env
TELEGRAM_WEB_APP_URL=https://your-domain.example
```

Then run:

```powershell
python configure_menu.py
```

`localhost.run` is useful for development, but its URLs are temporary.

## Spam Safety

`/spam` is intentionally limited:

- maximum 50 messages
- delay between messages
- cooldown
- group usage restricted to admins

This keeps the command usable for private/testing chats without turning the bot into an unwanted messaging tool.

## Configure Bot Profile

Commands and menu button are updated during normal startup. Profile text can be updated separately:

```powershell
python configure_profile.py
```

Do not run this often. Telegram applies long rate limits to profile changes.

Bot avatar cannot be changed through the Bot API. Set it manually in BotFather:

```text
/mybots -> your bot -> Edit Bot -> Edit Botpic
```

## Troubleshooting

### `Set TELEGRAM_BOT_TOKEN in environment or .env file`

Create `.env` and add:

```env
TELEGRAM_BOT_TOKEN=your_real_token_from_botfather
```

### Mini App shows `no tunnel here :(`

The temporary tunnel URL expired. Restart everything:

```powershell
powershell -ExecutionPolicy Bypass -File .\stop_all.ps1
powershell -ExecutionPolicy Bypass -File .\start_all.ps1
```

### URL opens in browser, but Telegram Mini App opens another/broken page

Telegram may still have an old menu button URL. Sync the exact working URL:

```powershell
python sync_tunnel_url.py https://your-current-url.lhr.life
```

Then fully close and reopen the Mini App in Telegram.

### Mini App opens, but `Надіслати боту` does not send

Open the bot chat and run:

```text
/app
```

Use the Web App button from the bot message. Some Telegram clients do not deliver `sendData()` when the app was opened from the persistent bottom menu button.

### `sync_tunnel_url.py` returns HTTP 503

The tunnel exists but is not connected to the local site yet, or the old URL was used. Restart the tunnel or use `start_all.ps1`, which waits until the tunnel is ready.

Also check that the local Mini App server is running:

```powershell
Invoke-WebRequest -Uri http://127.0.0.1:8787/ -UseBasicParsing
```

### Bot answers twice

Only one `bot.py` process should run. Stop all helpers:

```powershell
powershell -ExecutionPolicy Bypass -File .\stop_all.ps1
```

Then start again.

## Tests

Run unit tests:

```powershell
python -m unittest
```

Check Python syntax:

```powershell
python -m compileall .
```

## Notes

- `.env` is ignored and must stay local.
- `.env.example` is safe to commit.
- `tools/`, logs, screenshots, Chrome profiles, and Python cache files are ignored.
