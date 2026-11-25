"""A string-keyed hash table using linear probing."""

import math


class _Entry:
    __slots__ = ("key", "value")

    def __init__(self, key: str, value: str):
        self.key = key
        self.value = value


class LinearProbingHashTable:
    """An open-addressed table with optional load-factor-based resizing."""

    def __init__(self, capacity: int = 16, max_load: float | None = 1.0):
        if not isinstance(capacity, int) or isinstance(capacity, bool):
            raise TypeError("capacity must be an integer")
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if max_load is not None:
            if isinstance(max_load, bool) or not isinstance(max_load, (int, float)):
                raise TypeError("max_load must be a positive number or None")
            if not math.isfinite(max_load) or max_load <= 0 or max_load > 1:
                raise ValueError("max_load must be between zero and one")

        self._capacity = capacity
        self._max_load = max_load
        self._slots: list[_Entry | None] = [None] * capacity
        self._size = 0

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def load_factor(self) -> float:
        return self._size / self._capacity

    def __len__(self) -> int:
        return self._size

    def _bucket_index(self, key: str) -> int:
        value = 0
        for character in key:
            value = (31 * value + ord(character)) % self._capacity
        return value

    def hash_steps(self, key: str) -> list[tuple[str, int, int]]:
        value = 0
        steps = []
        for character in key:
            value = (31 * value + ord(character)) % self._capacity
            steps.append((character, ord(character), value))
        return steps

    def _find_slot(self, key: str) -> tuple[int | None, int]:
        index = self._bucket_index(key)
        for probes in range(1, self._capacity + 1):
            entry = self._slots[index]
            if entry is None or entry.key == key:
                return index, probes
            index = (index + 1) % self._capacity
        return None, self._capacity

    def find(self, key: str) -> tuple[str | None, int]:
        if not isinstance(key, str):
            raise TypeError("key must be a string")

        index, probes = self._find_slot(key)
        if index is None:
            return None, probes
        entry = self._slots[index]
        if entry is None:
            return None, probes
        return entry.value, probes

    def get(self, key: str) -> str | None:
        return self.find(key)[0]

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, str):
            return False
        return self.find(key)[0] is not None

    def put(self, key: str, value: str) -> None:
        if not isinstance(key, str):
            raise TypeError("key must be a string")

        index, _ = self._find_slot(key)
        if index is not None and self._slots[index] is not None:
            self._slots[index].value = value
            return

        if self._max_load is None:
            if index is None:
                raise OverflowError("hash table is full")
        else:
            while (self._size + 1) / self._capacity > self._max_load:
                self._resize()
            index, _ = self._find_slot(key)
            if index is None:
                raise OverflowError("hash table is full")

        self._slots[index] = _Entry(key, value)
        self._size += 1

    def probe_trace(self, key: str) -> tuple[int, list[int], int | None]:
        """Return the initial slot, inspected slots, and matching slot."""
        if not isinstance(key, str):
            raise TypeError("key must be a string")

        initial = self._bucket_index(key)
        index = initial
        visited = []
        for _ in range(self._capacity):
            visited.append(index)
            entry = self._slots[index]
            if entry is None:
                return initial, visited, None
            if entry.key == key:
                return initial, visited, index
            index = (index + 1) % self._capacity
        return initial, visited, None

    def _resize(self) -> None:
        old_slots = self._slots
        self._capacity *= 2
        self._slots = [None] * self._capacity
        for entry in old_slots:
            if entry is not None:
                index, _ = self._find_slot(entry.key)
                if index is None:
                    raise RuntimeError("resized table has no empty slot")
                self._slots[index] = entry
