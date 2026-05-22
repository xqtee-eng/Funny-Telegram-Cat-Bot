import random
import unittest

from text_tools import (
    MAX_RANDOM_WORDS,
    MAX_SPAM,
    caps_text,
    clap_text,
    emoji_text,
    lower_text,
    meme_text,
    mock_text,
    random_text,
    reverse_text,
    roast_text,
    shuffle_words,
    spam_messages,
    title_text,
    vaporwave_text,
)


class TextToolsTest(unittest.TestCase):
    def test_spam_messages_caps_message_count(self) -> None:
        result = spam_messages("hello", MAX_SPAM + 50)
        self.assertEqual(result, ["hello"] * MAX_SPAM)

    def test_mock_text_alternates_letters_only(self) -> None:
        self.assertEqual(mock_text("Ab c!"), "aB c!")

    def test_reverse_text(self) -> None:
        self.assertEqual(reverse_text("abc 123"), "321 cba")

    def test_case_commands(self) -> None:
        self.assertEqual(caps_text("привіт"), "ПРИВІТ")
        self.assertEqual(lower_text("ПРИВІТ"), "привіт")
        self.assertEqual(title_text("привіт світ"), "Привіт Світ")

    def test_shuffle_words_keeps_same_words(self) -> None:
        result = shuffle_words("one two three", random.Random(1))
        self.assertCountEqual(result.split(), ["one", "two", "three"])

    def test_shuffle_single_word_shuffles_characters(self) -> None:
        result = shuffle_words("abcd", random.Random(1))
        self.assertNotEqual(result, "abcd")
        self.assertCountEqual(result, "abcd")

    def test_clap_single_word_splits_letters(self) -> None:
        self.assertEqual(clap_text("ого"), "о 👏 г 👏 о")

    def test_emoji_text_adds_emoji(self) -> None:
        result = emoji_text("один два", random.Random(1))
        self.assertIn("один", result)
        self.assertIn("два", result)
        self.assertNotEqual(result, "один два")

    def test_emoji_text_uses_intensity(self) -> None:
        result = emoji_text("один два", random.Random(1), intensity=3)
        emoji_chunks = [part for part in result.split() if part not in {"один", "два"}]
        self.assertTrue(any(len(chunk) >= 3 for chunk in emoji_chunks))

    def test_meme_and_roast_include_text(self) -> None:
        self.assertIn("ідея", meme_text("ідея", random.Random(1)))
        self.assertIn("ідея", roast_text("ідея", random.Random(1)))

    def test_random_text_caps_word_count(self) -> None:
        result = random_text(MAX_RANDOM_WORDS + 100, random.Random(1))
        self.assertEqual(len(result.rstrip(".").split()), MAX_RANDOM_WORDS)

    def test_vaporwave_text_fullwidth_ascii(self) -> None:
        self.assertEqual(vaporwave_text("A! 1"), "Ａ！　１")

    def test_vaporwave_text_expands_cyrillic(self) -> None:
        self.assertEqual(vaporwave_text("ого"), "о　г　о")


if __name__ == "__main__":
    unittest.main()
