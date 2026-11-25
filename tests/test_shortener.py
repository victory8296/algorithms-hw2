import unittest

from src.shortener import expand, shorten


class ShortenerTests(unittest.TestCase):
    def test_shortens_and_expands_url_without_changing_it(self):
        url = "https://example.com/a/page?query=value"

        code = shorten(url)

        self.assertEqual(expand(code), url)

    def test_returns_existing_code_for_same_url(self):
        url = "https://same-url.example/path"

        first_code = shorten(url)

        self.assertEqual(shorten(url), first_code)

    def test_assigns_different_codes_to_different_urls(self):
        first_url = "https://example.com/first"
        second_url = "https://example.com/second"

        first_code = shorten(first_url)
        second_code = shorten(second_url)

        self.assertNotEqual(first_code, second_code)
        self.assertEqual(expand(first_code), first_url)
        self.assertEqual(expand(second_code), second_url)

    def test_url_length_boundary(self):
        prefix = "https://example.com/"
        url = prefix + "a" * (2048 - len(prefix))

        self.assertEqual(expand(shorten(url)), url)
        with self.assertRaises(ValueError):
            shorten(url + "a")

    def test_rejects_invalid_urls(self):
        invalid_urls = (
            "",
            " https://example.com",
            "https://example.com ",
            "ftp://example.com",
            "https://",
            "https://example.com/path with space",
        )

        for url in invalid_urls:
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    shorten(url)

    def test_returns_none_for_unregistered_code(self):
        self.assertIsNone(expand("zzzzzzzzzz"))

    def test_rejects_malformed_code(self):
        with self.assertRaises(ValueError):
            expand("!")


if __name__ == "__main__":
    unittest.main()
