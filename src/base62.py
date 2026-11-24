"""Base62 conversion using the alphabet 0-9, a-z, A-Z."""

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE = len(ALPHABET)


def encode(value: int) -> str:
    """Encode a non-negative integer as a base62 string."""
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError("value must be an integer")
    if value < 0:
        raise ValueError("value must be non-negative")
    if value == 0:
        return ALPHABET[0]

    encoded = []
    while value:
        value, remainder = divmod(value, BASE)
        encoded.append(ALPHABET[remainder])
    return "".join(reversed(encoded))


def decode(code: str) -> int:
    """Decode a base62 string into a non-negative integer."""
    if not isinstance(code, str):
        raise TypeError("code must be a string")
    if not code:
        raise ValueError("code must not be empty")

    value = 0
    for character in code:
        try:
            digit = ALPHABET.index(character)
        except ValueError:
            raise ValueError(f"invalid base62 character: {character!r}") from None
        value = value * BASE + digit
    return value
