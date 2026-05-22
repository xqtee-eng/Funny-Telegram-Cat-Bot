from pathlib import Path
import os

from bot import TelegramBot, TelegramRateLimitError, format_wait_time, load_dotenv


def main() -> None:
    load_dotenv(Path(".env"))
    bot = TelegramBot(os.environ["TELEGRAM_BOT_TOKEN"])
    try:
        bot.set_bot_commands()
        bot.set_bot_menu_button()
        bot.set_bot_profile()
        commands = bot.api("getMyCommands", {})["result"]
        profile = bot.api("getMe", {})["result"]
    except TelegramRateLimitError as error:
        print("Telegram тимчасово обмежив зміну профілю бота.")
        print(f"Спробуй ще раз через {format_wait_time(error.retry_after)}.")
        print("Сам бот може працювати далі; це обмеження тільки на налаштування профілю.")
        return

    print(profile.get("username", profile.get("id")))
    print(f"commands={len(commands)}")
    print("Profile configured.")


if __name__ == "__main__":
    main()
