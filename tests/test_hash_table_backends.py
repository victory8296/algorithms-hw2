import unittest

from src.hash_table import HashTable
from src.linear_probing import LinearProbingHashTable


BACKENDS = (
    ("chaining", HashTable),
    ("linear", LinearProbingHashTable),
)


class HashTableBackendTests(unittest.TestCase):
    def test_common_operations_and_legacy_resize_behavior(self):
        for name, table_type in BACKENDS:
            with self.subTest(backend=name):
                table = table_type()
                table.put("A", "first")
                table.put("Q", "second")

                self.assertEqual(table.get("A"), "first")
                self.assertEqual(table.get("Q"), "second")
                self.assertEqual(
                    table.find("A"), ("first", 2 if name == "chaining" else 1)
                )
                self.assertEqual(
                    table.find("missing"), (None, 0 if name == "chaining" else 1)
                )
                self.assertIn("A", table)
                self.assertNotIn("missing", table)
                self.assertEqual(len(table), 2)

                table.put("A", "updated")
                self.assertEqual(table.get("A"), "updated")
                self.assertEqual(len(table), 2)

                for number in range(14):
                    table.put(f"key-{number}", f"value-{number}")
                self.assertEqual(table.capacity, 16)
                table.put("seventeenth-key", "seventeenth-value")
                self.assertEqual(table.capacity, 32)
                self.assertEqual(table.get("A"), "updated")
                self.assertEqual(table.get("Q"), "second")
                self.assertEqual(table.load_factor, len(table) / table.capacity)

    def test_empty_failed_search_cost_matches_each_representation(self):
        chaining = HashTable(capacity=4, max_load=None)
        linear = LinearProbingHashTable(capacity=4, max_load=None)

        self.assertEqual(chaining.find("absent"), (None, 0))
        self.assertEqual(linear.find("absent"), (None, 1))
        self.assertEqual(chaining.load_factor, 0)
        self.assertEqual(linear.load_factor, 0)

    def test_linear_wraps_collision_cluster_and_counts_inspected_slots(self):
        table = LinearProbingHashTable(capacity=4, max_load=None)
        table.put("C", "value-c")
        table.put("G", "value-g")

        self.assertEqual(table._slots[3].key, "C")
        self.assertEqual(table._slots[0].key, "G")
        self.assertEqual(table.find("G"), ("value-g", 2))
        self.assertEqual(table.find("absent"), (None, 1))

    def test_full_fixed_linear_table_searches_once_per_slot_and_updates(self):
        table = LinearProbingHashTable(capacity=4, max_load=None)
        for key in ("A", "B", "C", "D"):
            table.put(key, f"value-{key}")

        self.assertEqual(table.find("missing"), (None, 4))
        with self.assertRaises(OverflowError):
            table.put("E", "value-E")

        table.put("B", "updated-B")
        self.assertEqual(table.get("B"), "updated-B")
        self.assertEqual(len(table), 4)
        self.assertEqual(table.find("missing"), (None, 4))


if __name__ == "__main__":
    unittest.main()
