from __future__ import annotations

import json
import math
import os
import socket
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from text_tools import (
    MAX_RANDOM_WORDS,
    MAX_SPAM,
    caps_text,
    clap_text,
    emoji_text,
    lower_text,
    meme_text,
    mock_text,
    random_effect,
    random_text,
    reverse_text,
    roast_text,
    shuffle_words,
    spam_messages,
    title_text,
    vaporwave_text,
    zalgo_text,
)


BOT_API_ROOT = "https://api.telegram.org/bot"
BOT_NAME = "FunnyBot"
BOT_SHORT_DESCRIPTION = "Прикольні штуки з текстом: random, emoji, meme, roast і spam."
BOT_DESCRIPTION = (
    "FunnyBot робить прикольні штуки з текстом: генерує рандом, перевертає слова, "
    "додає emoji, робить meme/roast, vaporwave, zalgo і обмежений spam окремими "
    "повідомленнями. Напиши /help або просто введи /, щоб побачити команди."
)
SINGLE_INSTANCE_HOST = "127.0.0.1"
SINGLE_INSTANCE_PORT = 47853
WEB_APP_URL_ENV = "TELEGRAM_WEB_APP_URL"
WEB_APP_BUTTON_TEXT = "Open"
SPAM_COOLDOWN_SECONDS = 15.0
SPAM_MESSAGE_DELAY_SECONDS = 0.45
PendingKey = tuple[int, int]


@dataclass(frozen=True)
class OutgoingMessage:
    text: str
    force_reply: bool = False
    placeholder: str | None = None
    reply_markup: dict[str, Any] | None = None


BotResponse = str | list[str] | OutgoingMessage
TEXT_COMMAND_HANDLERS: dict[str, Callable[[str], str]] = {
    "/caps": caps_text,
    "/lower": lower_text,
    "/title": title_text,
    "/mock": mock_text,
    "/reverse": reverse_text,
    "/shuffle": shuffle_words,
    "/clap": clap_text,
    "/emoji": emoji_text,
    "/vapor": vaporwave_text,
    "/zalgo": zalgo_text,
    "/meme": meme_text,
    "/roast": roast_text,
}

BOT_COMMANDS: tuple[tuple[str, str, str], ...] = (
    ("start", "/start", "Показати список команд"),
    ("help", "/help", "Показати список команд"),
    ("random", "/random [кількість]", f"Випадковий текст до {MAX_RANDOM_WORDS} слів"),
    ("caps", "/caps <текст>", "Зробити текст великими літерами"),
    ("lower", "/lower <текст>", "Зробити текст маленькими літерами"),
    ("title", "/title <текст>", "Кожне слово з великої літери"),
    ("mock", "/mock <текст>", "зРоБиТи оТаК"),
    ("reverse", "/reverse <текст>", "Перевернути текст"),
    ("shuffle", "/shuffle <текст>", "Перемішати слова або літери"),
    ("clap", "/clap <текст>", "Додати хлопки між словами"),
    ("emoji", "/emoji <текст>", "Додати рандомні emoji"),
    ("vapor", "/vapor <текст>", "Зробити vaporwave-стиль"),
    ("zalgo", "/zalgo <текст>", "Додати трохи хаосу"),
    ("meme", "/meme <текст>", "Зробити мемний шаблон"),
    ("roast", "/roast <текст>", "М'яко підсмажити текст"),
    ("spam", f"/spam <1-{MAX_SPAM}> <текст>", "Надіслати текст окремими повідомленнями"),
    ("app", "/app", "Відкрити Mini App"),
    ("cancel", "/cancel", "Скасувати команду, яка чекає текст"),
)

HELP_TEXT = (
    "Команди:\n"
    + "\n".join(f"{usage} - {description}" for _, usage, description in BOT_COMMANDS)
    + "\n\nКоманду можна надіслати без тексту, а потім окремо надіслати текст для ефекту."
    + "\nЯкщо просто надіслати текст без команди, бот застосує випадковий ефект."
)


class TelegramRateLimitError(RuntimeError):
    def __init__(self, retry_after: int) -> None:
        super().__init__(f"Telegram rate limit, retry after {retry_after}s")
        self.retry_after = retry_after


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip().lstrip("\ufeff")
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


class TelegramBot:
    def __init__(self, token: str) -> None:
        self.token = token
        self.last_spam_by_chat: dict[int, float] = {}
        self.pending_command_by_user: dict[PendingKey, str] = {}

    def api(self, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{BOT_API_ROOT}{self.token}/{method}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        timeout = int(payload.get("timeout", 20)) + 10
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            if error.code == 429:
                retry_after = parse_retry_after(body)
                raise TelegramRateLimitError(retry_after) from error
            raise RuntimeError(f"Telegram HTTP error for {method}: {error.code} {body}") from error
        result = json.loads(body)
        if not result.get("ok"):
            raise RuntimeError(f"Telegram API error for {method}: {result}")
        return result

    def send_message(
        self,
        chat_id: int,
        text: str,
        reply_to_message_id: int | None = None,
        reply_markup: dict[str, Any] | None = None,
    ) -> None:
        text = text or "Нічого не вийшло."
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "text": text[:4096],
            "disable_web_page_preview": True,
        }
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup
        if reply_to_message_id is not None:
            payload["reply_to_message_id"] = reply_to_message_id
            payload["allow_sending_without_reply"] = True
        try:
            self.api("sendMessage", payload)
        except TelegramRateLimitError as error:
            time.sleep(error.retry_after)
            self.api("sendMessage", payload)

    def set_bot_commands(self) -> None:
        self.api("setMyCommands", {"commands": bot_command_payload()})

    def set_bot_menu_button(self) -> None:
        web_app_url = os.environ.get(WEB_APP_URL_ENV, "").strip()
        if web_app_url:
            menu_button = {
                "type": "web_app",
                "text": WEB_APP_BUTTON_TEXT,
                "web_app": {"url": web_app_url},
            }
        else:
            menu_button = {"type": "commands"}
        self.api("setChatMenuButton", {"menu_button": menu_button})

    def set_bot_profile(self, force: bool = False) -> None:
        if force or self.get_profile_value("getMyName", "name") != BOT_NAME:
            self.api("setMyName", {"name": BOT_NAME})
        if (
            force
            or self.get_profile_value("getMyShortDescription", "short_description")
            != BOT_SHORT_DESCRIPTION
        ):
            self.api("setMyShortDescription", {"short_description": BOT_SHORT_DESCRIPTION})
        if force or self.get_profile_value("getMyDescription", "description") != BOT_DESCRIPTION:
            self.api("setMyDescription", {"description": BOT_DESCRIPTION})

    def get_profile_value(self, method: str, field: str) -> str:
        result = self.api(method, {})["result"]
        value = result.get(field, "")
        return value if isinstance(value, str) else ""

    def get_updates(self, offset: int | None, timeout: int = 50) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {
            "timeout": timeout,
            "allowed_updates": ["message"],
        }
        if offset is not None:
            payload["offset"] = offset
        result = self.api("getUpdates", payload)
        return result.get("result", [])

    def can_spam(self, chat_id: int) -> tuple[bool, int]:
        now = time.monotonic()
        last_time = self.last_spam_by_chat.get(chat_id, 0)
        remaining = SPAM_COOLDOWN_SECONDS - (now - last_time)
        if remaining > 0:
            return False, max(1, math.ceil(remaining))
        self.last_spam_by_chat[chat_id] = now
        return True, 0

    def is_chat_admin(self, chat_id: int, user_id: int) -> bool:
        try:
            result = self.api("getChatMember", {"chat_id": chat_id, "user_id": user_id})
        except (urllib.error.URLError, TimeoutError, RuntimeError):
            return False
        status = result.get("result", {}).get("status")
        return status in {"administrator", "creator"}

    def handle_update(self, update: dict[str, Any]) -> None:
        message = update.get("message")
        if not isinstance(message, dict):
            return

        chat = message.get("chat")
        if not isinstance(chat, dict):
            return

        chat_id = chat["id"]
        chat_type = chat.get("type", "private")
        user = message.get("from")
        user_id = user.get("id", 0) if isinstance(user, dict) else 0
        message_id = message.get("message_id")
        web_app_data = message.get("web_app_data")
        if isinstance(web_app_data, dict):
            response = self.handle_web_app_data(chat_id, user_id, web_app_data)
            self.send_response(chat_id, response, message_id)
            return

        text = message.get("text")
        if not isinstance(text, str):
            return

        reply_text = get_reply_text(message)
        response = self.handle_text(chat_id, user_id, text, reply_text, chat_type)
        self.send_response(chat_id, response, message_id)

    def send_response(
        self,
        chat_id: int,
        response: BotResponse,
        reply_to_message_id: int | None,
    ) -> None:
        response_messages = as_outgoing_messages(response)
        for index, response_message in enumerate(response_messages):
            response_reply_to_message_id = reply_to_message_id if index == 0 else None
            self.send_message(
                chat_id,
                response_message.text,
                response_reply_to_message_id,
                response_message.reply_markup or force_reply_markup(response_message),
            )
            if index < len(response_messages) - 1:
                time.sleep(SPAM_MESSAGE_DELAY_SECONDS)

    def handle_text(
        self,
        chat_id: int,
        user_id: int,
        text: str,
        reply_text: str | None = None,
        chat_type: str = "private",
    ) -> BotResponse:
        command, args = parse_command(text)
        pending_key = (chat_id, user_id)

        if not command:
            pending_command = self.pending_command_by_user.pop(pending_key, "")
            if pending_command:
                return apply_text_command(pending_command, text)
            effect_name, result = random_effect(text)
            return f"[{effect_name}]\n{result}"

        if command in {"/start", "/help"}:
            return HELP_TEXT

        if command == "/app":
            web_app_url = os.environ.get(WEB_APP_URL_ENV, "").strip()
            if not web_app_url:
                return (
                    "Mini App майже готова. Треба задеплоїти папку mini_app на HTTPS "
                    f"і записати URL у {WEB_APP_URL_ENV}."
                )
            return OutgoingMessage(
                text="Відкрий Mini App кнопкою нижче.",
                reply_markup=web_app_keyboard(web_app_url),
            )

        if command == "/cancel":
            if self.pending_command_by_user.pop(pending_key, None):
                return "Скасовано."
            return "Немає активної команди для скасування."

        if command == "/random":
            count = parse_int(args, default=12)
            return random_text(count)

        if command in TEXT_COMMAND_HANDLERS:
            if args:
                return apply_text_command(command, args)
            if reply_text:
                return apply_text_command(command, reply_text)
            self.pending_command_by_user[pending_key] = command
            return OutgoingMessage(
                text=f"Ок, напиши текст для {command} тут у відповідь.",
                force_reply=True,
                placeholder=f"Текст для {command}",
            )

        if command == "/spam":
            if chat_type in {"group", "supergroup"} and not self.is_chat_admin(chat_id, user_id):
                return "У групах /spam можуть запускати тільки адміни."
            times, spam_body = parse_spam_args(args)
            if not spam_body and reply_text:
                spam_body = reply_text
            if not spam_body:
                return f"Формат: /spam 3 текст. Максимум {MAX_SPAM} повідомлень."
            allowed, wait_seconds = self.can_spam(chat_id)
            if not allowed:
                return f"Зачекай ще {wait_seconds} с перед спамом."
            return spam_messages(spam_body, times)

        return "Не знаю таку команду. Напиши /help."

    def handle_web_app_data(
        self,
        chat_id: int,
        user_id: int,
        web_app_data: dict[str, Any],
    ) -> BotResponse:
        del user_id
        try:
            payload = json.loads(str(web_app_data.get("data", "{}")))
        except json.JSONDecodeError:
            return "Mini App надіслав некоректні дані."

        action = str(payload.get("action", "")).strip().lower()
        text = str(payload.get("text", "")).strip()
        if action == "random":
            count = parse_int(str(payload.get("count", "12")), default=12)
            return random_text(count)
        if not text:
            return "Mini App: додай текст."

        if action == "spam":
            times = parse_int(str(payload.get("count", "3")), default=3)
            allowed, wait_seconds = self.can_spam(chat_id)
            if not allowed:
                return f"Зачекай ще {wait_seconds} с перед спамом."
            return spam_messages(text, times)

        intensity = parse_int(str(payload.get("intensity", "2")), default=2)
        if action == "emoji":
            return emoji_text(text, intensity=intensity)
        if action == "zalgo":
            return zalgo_text(text, intensity=intensity)

        command = f"/{action}"
        if command not in TEXT_COMMAND_HANDLERS:
            return "Mini App: невідомий ефект."
        return apply_text_command(command, text)

    def run(self) -> None:
        self.configure_command_menu()
        offset = self.initial_offset()
        print("Bot is running. Press Ctrl+C to stop.")
        while True:
            try:
                for update in self.get_updates(offset):
                    self.handle_update(update)
                    offset = update["update_id"] + 1
            except KeyboardInterrupt:
                print("\nBot stopped.")
                return
            except (urllib.error.URLError, TimeoutError, RuntimeError) as error:
                print(f"Polling error: {error}", file=sys.stderr)
                time.sleep(3)

    def initial_offset(self) -> int | None:
        try:
            updates = self.get_updates(None, timeout=0)
        except (urllib.error.URLError, TimeoutError, RuntimeError) as error:
            print(f"Could not skip old updates: {error}", file=sys.stderr)
            return None
        if not updates:
            return None
        offset = updates[-1]["update_id"] + 1
        print(f"Skipped {len(updates)} old update(s).")
        return offset

    def configure_command_menu(self) -> None:
        try:
            self.set_bot_commands()
            self.set_bot_menu_button()
        except (urllib.error.URLError, TimeoutError, RuntimeError) as error:
            print(f"Could not configure command menu: {error}", file=sys.stderr)


def parse_command(text: str) -> tuple[str, str]:
    if not text.startswith("/"):
        return "", text

    first, _, rest = text.partition(" ")
    command = first.split("@", 1)[0].lower()
    return command, rest.strip()


def bot_command_payload() -> list[dict[str, str]]:
    return [
        {"command": command, "description": description}
        for command, _, description in BOT_COMMANDS
    ]


def web_app_keyboard(web_app_url: str) -> dict[str, Any]:
    return {
        "keyboard": [
            [
                {
                    "text": "Відкрити Mini App",
                    "web_app": {"url": web_app_url},
                }
            ]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
    }


def get_reply_text(message: dict[str, Any]) -> str | None:
    reply = message.get("reply_to_message")
    if not isinstance(reply, dict):
        return None
    text = reply.get("text")
    return text if isinstance(text, str) and text.strip() else None


def parse_retry_after(body: str) -> int:
    try:
        payload = json.loads(body)
        retry_after = int(payload.get("parameters", {}).get("retry_after", 3))
    except (TypeError, ValueError, json.JSONDecodeError):
        return 3
    return max(1, retry_after)


def format_wait_time(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts: list[str] = []
    if hours:
        parts.append(f"{hours} год")
    if minutes:
        parts.append(f"{minutes} хв")
    if seconds or not parts:
        parts.append(f"{seconds} с")
    return " ".join(parts)


def parse_int(value: str, default: int) -> int:
    try:
        first = value.strip().split(maxsplit=1)[0]
        return int(first)
    except (IndexError, ValueError):
        return default


def parse_spam_args(args: str) -> tuple[int, str]:
    first, _, rest = args.strip().partition(" ")
    if not first:
        return 1, ""

    try:
        times = int(first)
        return times, rest.strip()
    except ValueError:
        return 3, args.strip()


def apply_text_command(command: str, text: str) -> str:
    handler = TEXT_COMMAND_HANDLERS[command]
    return handler(text)


def as_outgoing_messages(response: BotResponse) -> list[OutgoingMessage]:
    if isinstance(response, str):
        return [OutgoingMessage(response)]
    if isinstance(response, OutgoingMessage):
        return [response]
    return [OutgoingMessage(text) for text in response]


def force_reply_markup(message: OutgoingMessage) -> dict[str, Any] | None:
    if not message.force_reply:
        return None
    markup: dict[str, Any] = {"force_reply": True, "selective": True}
    if message.placeholder:
        markup["input_field_placeholder"] = message.placeholder[:64]
    return markup


def acquire_single_instance_lock(
    host: str = SINGLE_INSTANCE_HOST,
    port: int = SINGLE_INSTANCE_PORT,
) -> socket.socket:
    lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        lock_socket.bind((host, port))
        lock_socket.listen(1)
    except OSError as error:
        lock_socket.close()
        raise RuntimeError("Bot is already running in another process.") from error
    return lock_socket


def main() -> None:
    try:
        lock_socket = acquire_single_instance_lock()
    except RuntimeError as error:
        print(error, file=sys.stderr)
        raise SystemExit(1)

    load_dotenv(Path(".env"))
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Set TELEGRAM_BOT_TOKEN in environment or .env file.", file=sys.stderr)
        raise SystemExit(1)

    try:
        TelegramBot(token).run()
    finally:
        lock_socket.close()


if __name__ == "__main__":
    main()
