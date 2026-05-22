import os
import unittest
from unittest.mock import patch

from bot import (
    BOT_COMMANDS,
    BOT_DESCRIPTION,
    BOT_NAME,
    BOT_SHORT_DESCRIPTION,
    HELP_TEXT,
    OutgoingMessage,
    TelegramBot,
    WEB_APP_URL_ENV,
    acquire_single_instance_lock,
    as_outgoing_messages,
    bot_command_payload,
    force_reply_markup,
    format_wait_time,
    language_status_text,
    normalize_language_code,
    parse_retry_after,
    web_app_keyboard,
)


class AdminAwareBot(TelegramBot):
    def __init__(self, status: str) -> None:
        super().__init__("token")
        self.status = status

    def api(self, method: str, payload: dict) -> dict:
        if method == "getChatMember":
            return {"ok": True, "result": {"status": self.status}}
        return super().api(method, payload)


class ProfileAwareBot(TelegramBot):
    def __init__(self) -> None:
        super().__init__("token")
        self.set_calls: list[str] = []

    def api(self, method: str, payload: dict) -> dict:
        if method == "getMyName":
            return {"ok": True, "result": {"name": BOT_NAME}}
        if method == "getMyShortDescription":
            return {"ok": True, "result": {"short_description": BOT_SHORT_DESCRIPTION}}
        if method == "getMyDescription":
            return {"ok": True, "result": {"description": BOT_DESCRIPTION}}
        if method.startswith("setMy"):
            self.set_calls.append(method)
            return {"ok": True, "result": True}
        return super().api(method, payload)


class MenuAwareBot(TelegramBot):
    def __init__(self) -> None:
        super().__init__("token")
        self.menu_payload: dict | None = None

    def api(self, method: str, payload: dict) -> dict:
        if method == "setChatMenuButton":
            self.menu_payload = payload
            return {"ok": True, "result": True}
        return super().api(method, payload)


class BotCommandTest(unittest.TestCase):
    def test_text_command_can_use_next_message(self) -> None:
        bot = TelegramBot("token")
        response = bot.handle_text(1, 10, "/reverse")
        self.assertIsInstance(response, OutgoingMessage)
        self.assertEqual(response.text, "Ок, напиши текст для /reverse тут у відповідь.")
        self.assertTrue(response.force_reply)
        self.assertEqual(bot.handle_text(1, 10, "привіт"), "тівирп")

    def test_text_command_can_use_reply_text(self) -> None:
        bot = TelegramBot("token")
        self.assertEqual(bot.handle_text(1, 10, "/reverse", "привіт"), "тівирп")

    def test_pending_command_is_per_user(self) -> None:
        bot = TelegramBot("token")
        response = bot.handle_text(1, 10, "/reverse")
        self.assertIsInstance(response, OutgoingMessage)
        bot.handle_text(1, 20, "/mock")
        self.assertEqual(bot.handle_text(1, 10, "привіт"), "тівирп")
        self.assertEqual(bot.handle_text(1, 20, "привіт"), "пРиВіТ")

    def test_cancel_clears_pending_command(self) -> None:
        bot = TelegramBot("token")
        bot.handle_text(1, 10, "/reverse")
        self.assertEqual(bot.handle_text(1, 10, "/cancel"), "Скасовано.")
        self.assertNotIn((1, 10), bot.pending_command_by_user)

    def test_spam_returns_separate_messages(self) -> None:
        bot = TelegramBot("token")
        self.assertEqual(bot.handle_text(1, 10, "/spam 3 привіт"), ["привіт"] * 3)

    def test_spam_can_use_reply_text(self) -> None:
        bot = TelegramBot("token")
        self.assertEqual(bot.handle_text(1, 10, "/spam 2", "привіт"), ["привіт"] * 2)

    def test_group_spam_requires_admin(self) -> None:
        bot = AdminAwareBot("member")
        self.assertEqual(
            bot.handle_text(1, 10, "/spam 2 привіт", chat_type="supergroup"),
            "У групах /spam можуть запускати тільки адміни.",
        )

    def test_group_spam_allows_admin(self) -> None:
        bot = AdminAwareBot("administrator")
        self.assertEqual(
            bot.handle_text(1, 10, "/spam 2 привіт", chat_type="supergroup"),
            ["привіт"] * 2,
        )

    def test_repeat_command_is_removed(self) -> None:
        bot = TelegramBot("token")
        self.assertEqual(bot.handle_text(1, 10, "/repeat 2 привіт"), "Не знаю таку команду. Напиши /help.")

    def test_start_reports_user_language(self) -> None:
        bot = TelegramBot("token")
        response = bot.handle_text(1, 10, "/start", language_code="uk")
        self.assertIn("Українська (uk)", response)
        self.assertIn("/random", response)

    def test_language_command_reports_unknown_language(self) -> None:
        bot = TelegramBot("token")
        self.assertEqual(
            bot.handle_text(1, 10, "/language"),
            "Системна мова Telegram: не вдалось визначити.",
        )

    def test_language_helpers_normalize_region_codes(self) -> None:
        self.assertEqual(normalize_language_code("uk-UA"), "uk")
        self.assertEqual(normalize_language_code("en_US"), "en")
        self.assertEqual(language_status_text("en-US"), "Системна мова Telegram: English (en-US).")

    def test_app_command_requires_url(self) -> None:
        bot = TelegramBot("token")
        with patch.dict(os.environ, {WEB_APP_URL_ENV: ""}, clear=False):
            self.assertIn(WEB_APP_URL_ENV, bot.handle_text(1, 10, "/app"))

    def test_app_command_returns_keyboard_when_url_exists(self) -> None:
        bot = TelegramBot("token")
        with patch.dict(os.environ, {WEB_APP_URL_ENV: "https://example.com/app"}, clear=False):
            response = bot.handle_text(1, 10, "/app")
        self.assertIsInstance(response, OutgoingMessage)
        self.assertEqual(response.reply_markup, web_app_keyboard("https://example.com/app"))

    def test_web_app_data_applies_effect(self) -> None:
        bot = TelegramBot("token")
        data = {"data": '{"action":"reverse","text":"привіт"}'}
        self.assertEqual(bot.handle_web_app_data(1, 10, data), "тівирп")

    def test_web_app_data_spam(self) -> None:
        bot = TelegramBot("token")
        data = {"data": '{"action":"spam","text":"го","count":2}'}
        self.assertEqual(bot.handle_web_app_data(1, 10, data), ["го", "го"])

    def test_web_app_data_random_does_not_require_input_text(self) -> None:
        bot = TelegramBot("token")
        data = {"data": '{"action":"random","text":"","count":4}'}
        self.assertEqual(len(str(bot.handle_web_app_data(1, 10, data)).rstrip(".").split()), 4)

    def test_web_app_data_zalgo_uses_intensity(self) -> None:
        bot = TelegramBot("token")
        data = {"data": '{"action":"zalgo","text":"а","intensity":5}'}
        self.assertGreaterEqual(len(str(bot.handle_web_app_data(1, 10, data))), 6)

    def test_parse_retry_after(self) -> None:
        self.assertEqual(parse_retry_after('{"parameters":{"retry_after":7}}'), 7)
        self.assertEqual(parse_retry_after("not-json"), 3)

    def test_format_wait_time(self) -> None:
        self.assertEqual(format_wait_time(85737), "23 год 48 хв 57 с")

    def test_bot_command_payload_matches_telegram_format(self) -> None:
        payload = bot_command_payload()
        self.assertEqual(len(payload), len(BOT_COMMANDS))
        for command in payload:
            self.assertNotIn("/", command["command"])
            self.assertTrue(command["description"])
            self.assertLessEqual(len(command["description"]), 256)

    def test_help_text_contains_all_command_usages(self) -> None:
        for _, usage, _ in BOT_COMMANDS:
            self.assertIn(usage, HELP_TEXT)

    def test_profile_texts_fit_telegram_limits(self) -> None:
        self.assertLessEqual(len(BOT_NAME), 64)
        self.assertLessEqual(len(BOT_SHORT_DESCRIPTION), 120)
        self.assertLessEqual(len(BOT_DESCRIPTION), 512)

    def test_set_bot_profile_skips_unchanged_fields(self) -> None:
        bot = ProfileAwareBot()
        bot.set_bot_profile()
        self.assertEqual(bot.set_calls, [])

    def test_single_instance_lock_uses_socket(self) -> None:
        lock = acquire_single_instance_lock(port=0)
        try:
            self.assertIsNotNone(lock.getsockname())
        finally:
            lock.close()

    def test_force_reply_markup(self) -> None:
        message = OutgoingMessage("Напиши текст", force_reply=True, placeholder="Текст")
        self.assertEqual(
            force_reply_markup(message),
            {"force_reply": True, "selective": True, "input_field_placeholder": "Текст"},
        )

    def test_as_outgoing_messages_wraps_strings_and_lists(self) -> None:
        self.assertEqual(as_outgoing_messages("hi"), [OutgoingMessage("hi")])
        self.assertEqual(
            as_outgoing_messages(["a", "b"]),
            [OutgoingMessage("a"), OutgoingMessage("b")],
        )

    def test_set_bot_menu_button_uses_web_app_url_when_present(self) -> None:
        bot = MenuAwareBot()
        with patch.dict(os.environ, {WEB_APP_URL_ENV: "https://example.com/app"}, clear=False):
            bot.set_bot_menu_button()
        self.assertEqual(
            bot.menu_payload,
            {
                "menu_button": {
                    "type": "web_app",
                    "text": "Open",
                    "web_app": {"url": "https://example.com/app"},
                }
            },
        )


if __name__ == "__main__":
    unittest.main()
