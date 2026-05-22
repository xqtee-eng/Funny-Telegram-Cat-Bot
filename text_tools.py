from __future__ import annotations

import random
import re
from collections.abc import Callable, Sequence


MAX_SPAM = 50
MAX_RANDOM_WORDS = 120
MAX_INPUT_CHARS = 900
MAX_SPAM_TEXT_CHARS = 400

EMOJIS = (
    "😂",
    "🔥",
    "💀",
    "🤯",
    "✨",
    "🫠",
    "😎",
    "🥔",
    "🚀",
    "🍕",
    "🧃",
    "🪩",
    "🤌",
    "📢",
    "🧀",
    "🫡",
)

MEME_TEMPLATES = (
    "Коли {text}, але батон уже в космосі.",
    "{text}? Звучить як план на 3 ночі і 2 нервові зриви.",
    "Мама: не роби {text}. Я через 5 хвилин: {text}.",
    "POV: ти відкрив чат, а там {text}.",
    "Науковці досі не пояснили феномен: {text}.",
    "Якщо життя дало тобі {text}, зроби з цього мем.",
    "Це не баг, це {text} в режимі турбо.",
    "У паралельному всесвіті {text} уже стало державною програмою.",
)

ROAST_TEMPLATES = (
    "{text}? Це звучить як план, який писали на серветці в маршрутці.",
    "{text} має вайб презентації, зробленої за 7 хвилин до дедлайну.",
    "{text} настільки впевнене, що навіть калькулятор попросив паузу.",
    "{text} зайшло в чат і одразу зробило вигляд, що так і треба.",
    "{text} виглядає як ідея, яку придумали після третьої кави.",
    "{text} не провал, просто дуже смілива версія хаосу.",
)

RANDOM_WORDS = (
    "капібара",
    "шаурма",
    "космос",
    "клавіатура",
    "пельмень",
    "турбо",
    "желейний",
    "мемний",
    "піксель",
    "чайник",
    "нічний",
    "генератор",
    "рандом",
    "печиво",
    "квест",
    "нейронка",
    "борщ",
    "магічний",
    "план",
    "текст",
    "хаос",
    "ультра",
    "дивний",
    "сирник",
    "батон",
    "драма",
    "кіт",
    "сміх",
    "банан",
    "телепорт",
    "режим",
    "кнопка",
    "пухнастий",
    "супчик",
    "галактичний",
    "сосиска",
    "комбайн",
    "міністр",
    "піжама",
    "танцюрист",
    "директор",
    "жабка",
    "шалений",
    "зозуля",
    "пиріжок",
    "кнопкодав",
    "мегафон",
    "каструля",
    "стікер",
    "хрумкий",
    "пилосос",
    "шкарпетка",
    "кринж",
    "легендарний",
    "трамвай",
    "сирний",
    "пончик",
    "бургер",
    "мікрохвильовка",
    "картопля",
    "бульбашка",
    "лохина",
    "ракета",
    "сонний",
    "жужик",
    "кава",
    "пульт",
    "тапок",
    "понеділок",
    "дискотека",
    "мурашки",
    "планета",
    "супергерой",
    "йогурт",
    "сковорідка",
    "сирена",
    "хмаринка",
    "креветка",
    "паляниця",
    "смішнючий",
    "кнопочка",
    "глюк",
    "батискаф",
    "фікус",
    "сарделька",
    "мемолог",
    "танк",
    "пельменатор",
    "карамельний",
    "калькулятор",
    "шашлик",
    "квадробер",
    "фантазер",
    "суперклей",
    "блискавка",
    "дзвіночок",
    "вареник",
    "завгосп",
    "інопланетянин",
    "гарбуз",
    "шахрайський",
    "хом'як",
    "космічний",
    "желе",
    "клавіша",
    "круасан",
    "пранк",
    "чебурек",
    "турбобатон",
    "салат",
    "магнітофон",
    "екскаватор",
    "сюрприз",
    "вайб",
)

ZALGO_MARKS = (
    "\u0300",
    "\u0301",
    "\u0302",
    "\u0303",
    "\u0304",
    "\u0306",
    "\u0307",
    "\u0308",
    "\u0309",
    "\u030a",
    "\u030b",
    "\u030c",
)


def trim_text(text: str, limit: int = MAX_INPUT_CHARS) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip()


def clamp_int(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


def random_text(word_count: int = 12, rng: random.Random | None = None) -> str:
    rng = rng or random
    word_count = clamp_int(word_count, 1, MAX_RANDOM_WORDS)
    words = [rng.choice(RANDOM_WORDS) for _ in range(word_count)]
    sentence = " ".join(words)
    return sentence[:1].upper() + sentence[1:] + "."


def mock_text(text: str) -> str:
    text = trim_text(text)
    upper = False
    result: list[str] = []
    for char in text:
        if char.isalpha():
            result.append(char.upper() if upper else char.lower())
            upper = not upper
        else:
            result.append(char)
    return "".join(result)


def reverse_text(text: str) -> str:
    return trim_text(text)[::-1]


def caps_text(text: str) -> str:
    return trim_text(text).upper()


def lower_text(text: str) -> str:
    return trim_text(text).lower()


def title_text(text: str) -> str:
    return trim_text(text).title()


def shuffle_words(text: str, rng: random.Random | None = None) -> str:
    rng = rng or random
    words = re.findall(r"\S+", trim_text(text))
    if len(words) == 1:
        return shuffle_characters(words[0], rng)
    rng.shuffle(words)
    return " ".join(words)


def shuffle_characters(text: str, rng: random.Random | None = None) -> str:
    rng = rng or random
    chars = list(text)
    if len(chars) < 2:
        return text

    original = "".join(chars)
    for _ in range(5):
        rng.shuffle(chars)
        shuffled = "".join(chars)
        if shuffled != original:
            return shuffled
    return original[1:] + original[:1]


def clap_text(text: str) -> str:
    words = re.findall(r"\S+", trim_text(text))
    if len(words) == 1:
        return " \U0001f44f ".join(words[0])
    return " \U0001f44f ".join(words)


def emoji_text(text: str, rng: random.Random | None = None, intensity: int = 1) -> str:
    rng = rng or random
    intensity = clamp_int(intensity, 1, 5)
    words = re.findall(r"\S+", trim_text(text))
    if not words:
        return ""
    if len(words) == 1:
        return f" {''.join(rng.choice(EMOJIS) for _ in range(intensity))} ".join(words[0])

    result: list[str] = []
    for index, word in enumerate(words):
        result.append(word)
        if index < len(words) - 1:
            result.append("".join(rng.choice(EMOJIS) for _ in range(intensity)))
    result.append("".join(rng.choice(EMOJIS) for _ in range(intensity)))
    return " ".join(result)


def vaporwave_text(text: str) -> str:
    result: list[str] = []
    text = trim_text(text)
    for index, char in enumerate(text):
        code = ord(char)
        if char == " ":
            result.append("\u3000")
        elif 33 <= code <= 126:
            result.append(chr(code + 0xFEE0))
        else:
            result.append(char)
            next_char = text[index + 1] if index + 1 < len(text) else ""
            if char.isalnum() and next_char.isalnum() and not next_char.isascii():
                result.append("\u3000")
    return "".join(result)


def zalgo_text(text: str, rng: random.Random | None = None, intensity: int | None = None) -> str:
    rng = rng or random
    result: list[str] = []
    for char in trim_text(text, 300):
        result.append(char)
        if char.strip():
            mark_count = clamp_int(intensity, 1, 5) if intensity is not None else rng.randint(1, 3)
            result.extend(rng.choice(ZALGO_MARKS) for _ in range(mark_count))
    return "".join(result)


def meme_text(text: str, rng: random.Random | None = None) -> str:
    rng = rng or random
    text = trim_text(text, 160)
    return rng.choice(MEME_TEMPLATES).format(text=text)


def roast_text(text: str, rng: random.Random | None = None) -> str:
    rng = rng or random
    text = trim_text(text, 160)
    return rng.choice(ROAST_TEMPLATES).format(text=text)


def spam_messages(text: str, times: int) -> list[str]:
    text = trim_text(text, MAX_SPAM_TEXT_CHARS)
    times = clamp_int(times, 1, MAX_SPAM)
    return [text for _ in range(times)]


def random_effect(text: str, rng: random.Random | None = None) -> tuple[str, str]:
    rng = rng or random
    effects: Sequence[tuple[str, Callable[[str], str]]] = (
        ("caps", caps_text),
        ("lower", lower_text),
        ("title", title_text),
        ("mock", mock_text),
        ("reverse", reverse_text),
        ("shuffle", lambda value: shuffle_words(value, rng)),
        ("clap", clap_text),
        ("emoji", lambda value: emoji_text(value, rng)),
        ("vapor", vaporwave_text),
        ("zalgo", lambda value: zalgo_text(value, rng)),
        ("meme", lambda value: meme_text(value, rng)),
        ("roast", lambda value: roast_text(value, rng)),
    )
    name, effect = rng.choice(effects)
    return name, effect(text)
