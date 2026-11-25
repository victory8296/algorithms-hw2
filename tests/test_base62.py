import unittest

from src.base62 import decode, encode


class Base62Tests(unittest.TestCase):
    def test_encodes_zero_and_alphabet_boundaries(self):
        self.assertEqual(encode(0), "0")
        self.assertEqual(encode(61), "Z")
        self.assertEqual(encode(62), "10")

    def test_round_trips_large_integer(self):
        value = 2**256
        self.assertEqual(decode(encode(value)), value)

    def test_decodes_case_sensitive_digits(self):
        self.assertEqual(decode("a"), 10)
        self.assertEqual(decode("A"), 36)

    def test_rejects_invalid_values(self):
        with self.assertRaises(ValueError):
            encode(-1)
        with self.assertRaises(ValueError):
            decode("")
        with self.assertRaises(ValueError):
            decode("!")
        with self.assertRaises(TypeError):
            encode(True)
        with self.assertRaises(TypeError):
            decode(1)


if __name__ == "__main__":
    unittest.main()
