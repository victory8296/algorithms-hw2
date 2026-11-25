"""A string-keyed hash table using separate chaining."""


class _Node:
    __slots__ = ("key", "value", "next")

    def __init__(self, key: str, value: str, next_node: "_Node | None" = None):
        self.key = key
        self.value = value
        self.next = next_node


class HashTable:
    """A hash table that resizes when its load factor exceeds one."""

    def __init__(self):
        self._capacity = 16
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
        if self._size > self._capacity:
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
