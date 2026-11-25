"""A string-keyed hash table using separate chaining."""

import math


class _Node:
    __slots__ = ("key", "value", "next")

    def __init__(self, key: str, value: str, next_node: "_Node | None" = None):
        self.key = key
        self.value = value
        self.next = next_node


class HashTable:
    """A string-keyed table with optional load-factor-based resizing."""

    def __init__(self, capacity: int = 16, max_load: float | None = 1.0):
        if not isinstance(capacity, int) or isinstance(capacity, bool):
            raise TypeError("capacity must be an integer")
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if max_load is not None:
            if isinstance(max_load, bool) or not isinstance(max_load, (int, float)):
                raise TypeError("max_load must be a positive number or None")
            if not math.isfinite(max_load) or max_load <= 0:
                raise ValueError("max_load must be positive and finite")

        self._capacity = capacity
        self._max_load = max_load
        self._buckets: list[_Node | None] = [None] * self._capacity
        self._size = 0

    @property
    def capacity(self) -> int:
        return self._capacity

    def __len__(self) -> int:
        return self._size

    def _bucket_index(self, key: str) -> int:
        value = 0
        for character in key:
            value = (31 * value + ord(character)) % self._capacity
        return value

    def put(self, key: str, value: str) -> None:
        if not isinstance(key, str):
            raise TypeError("key must be a string")

        index = self._bucket_index(key)
        node = self._buckets[index]
        while node is not None:
            if node.key == key:
                node.value = value
                return
            node = node.next

        self._buckets[index] = _Node(key, value, self._buckets[index])
        self._size += 1
        if self._max_load is not None:
            while self._size / self._capacity > self._max_load:
                self._resize()

    def get(self, key: str) -> str | None:
        if not isinstance(key, str):
            raise TypeError("key must be a string")

        node = self._buckets[self._bucket_index(key)]
        while node is not None:
            if node.key == key:
                return node.value
            node = node.next
        return None

    def _resize(self) -> None:
        old_buckets = self._buckets
        self._capacity *= 2
        self._buckets = [None] * self._capacity

        for head in old_buckets:
            node = head
            while node is not None:
                next_node = node.next
                index = self._bucket_index(node.key)
                node.next = self._buckets[index]
                self._buckets[index] = node
                node = next_node
