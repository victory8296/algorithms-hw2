import unittest

from src.hash_table import HashTable


class HashTableTests(unittest.TestCase):
    def test_stores_and_retrieves_colliding_keys(self):
        table = HashTable()
        table.put("A", "first value")
        table.put("Q", "second value")

        self.assertEqual(table.get("A"), "first value")
        self.assertEqual(table.get("Q"), "second value")

    def test_overwrites_existing_key_without_losing_colliding_key(self):
        table = HashTable()
        table.put("A", "original value")
        table.put("Q", "other value")

        table.put("A", "updated value")

        self.assertEqual(len(table), 2)
        self.assertEqual(table.get("A"), "updated value")
        self.assertEqual(table.get("Q"), "other value")

    def test_returns_none_for_missing_key(self):
        self.assertIsNone(HashTable().get("zz"))

    def test_resizes_after_seventeenth_key_and_preserves_entries(self):
        table = HashTable()
        keys = "0123456789abcdef"

        for key in keys:
            table.put(key, f"value for {key}")

        self.assertEqual(table.capacity, 16)
        table.put("a", "updated value for a")
        self.assertEqual(table.capacity, 16)

        table.put("g", "value for g")

        self.assertEqual(table.capacity, 32)
        self.assertEqual(table.get("a"), "updated value for a")
        self.assertEqual(table.get("g"), "value for g")
        for key in keys:
            if key != "a":
                self.assertEqual(table.get(key), f"value for {key}")


if __name__ == "__main__":
    unittest.main()
