from __future__ import annotations

import os
import re
import urllib.request
from pathlib import Path

from bot import WEB_APP_URL_ENV, TelegramBot, load_dotenv


LOG_PATH = Path("localhostrun.out.log")
ENV_PATH = Path(".env")


def find_latest_tunnel_url(log_path: Path = LOG_PATH) -> str:
    if not log_path.exists():
        raise RuntimeError(f"{log_path} not found.")

    content = log_path.read_text(encoding="utf-8", errors="ignore")
    urls = re.findall(r"https://[a-z0-9-]+\.lhr\.life", content)
    if not urls:
        raise RuntimeError("No localhost.run HTTPS URL found in tunnel log.")
    return urls[-1]


def assert_url_works(url: str) -> None:
    with urllib.request.urlopen(url, timeout=10) as response:
        if response.status != 200:
            raise RuntimeError(f"{url} returned HTTP {response.status}.")


def update_env_value(path: Path, key: str, value: str) -> None:
    lines = path.read_text(encoding="utf-8-sig").splitlines() if path.exists() else []
    key_prefix = f"{key}="
    updated = False
    new_lines: list[str] = []
    for line in lines:
        if line.startswith(key_prefix):
            new_lines.append(f"{key}={value}")
            updated = True
        else:
            new_lines.append(line)
    if not updated:
        new_lines.append(f"{key}={value}")
    path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def main() -> None:
    url = find_latest_tunnel_url()
    assert_url_works(url)
    update_env_value(ENV_PATH, WEB_APP_URL_ENV, url)

    load_dotenv(ENV_PATH)
    os.environ[WEB_APP_URL_ENV] = url
    bot = TelegramBot(os.environ["TELEGRAM_BOT_TOKEN"])
    bot.set_bot_commands()
    bot.set_bot_menu_button()
    menu_button = bot.api("getChatMenuButton", {})["result"]

    print(f"web_app_url={url}")
    print(f"menu_button={menu_button.get('type')}")


if __name__ == "__main__":
    main()
