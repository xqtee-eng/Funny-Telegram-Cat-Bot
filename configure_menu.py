from pathlib import Path
import os

from bot import WEB_APP_URL_ENV, TelegramBot, load_dotenv


def main() -> None:
    load_dotenv(Path(".env"))
    bot = TelegramBot(os.environ["TELEGRAM_BOT_TOKEN"])
    bot.set_bot_commands()
    bot.set_bot_menu_button()
    commands = bot.api("getMyCommands", {})["result"]
    menu_button = bot.api("getChatMenuButton", {})["result"]
    print(f"commands={len(commands)}")
    print(f"web_app_url={os.environ.get(WEB_APP_URL_ENV, '')}")
    print(f"menu_button={menu_button.get('type')}")


if __name__ == "__main__":
    main()
