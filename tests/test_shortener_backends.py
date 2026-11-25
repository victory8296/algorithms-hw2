import unittest

from src.shortener import URLShortener


class ShortenerBackendTests(unittest.TestCase):
    def test_shortener_behavior_is_shared_by_both_backends(self):
        for backend in ("chaining", "linear"):
            with self.subTest(backend=backend):
                shortener = URLShortener(backend=backend)
                first_url = "https://example.com/a/page?query=value"
                second_url = "https://example.com/another"

                first_code = shortener.shorten(first_url)
                second_code = shortener.shorten(second_url)

                self.assertNotEqual(first_code, second_code)
                self.assertEqual(shortener.expand(first_code), first_url)
                self.assertEqual(shortener.shorten(first_url), first_code)
                self.assertIsNone(shortener.expand("zzzzzzzzzz"))
                with self.assertRaises(ValueError):
                    shortener.expand("!")

                for url in (
                    "",
                    " https://example.com",
                    "ftp://example.com",
                    "https://",
                    "https://example.com/path with space",
                ):
                    with self.subTest(backend=backend, url=url):
                        with self.assertRaises(ValueError):
                            shortener.shorten(url)

    def test_default_module_functions_remain_chaining_compatible(self):
        from src.shortener import expand, shorten

        url = "https://module-api.example/path"
        self.assertEqual(expand(shorten(url)), url)


if __name__ == "__main__":
    unittest.main()
