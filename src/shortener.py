"""In-memory URL shortening backed by custom hash tables."""

from urllib.parse import urlsplit

from src.base62 import decode, encode
from src.hash_table import HashTable
from src.linear_probing import LinearProbingHashTable


def _validate_url(url: str) -> None:
    if not isinstance(url, str):
        raise ValueError("url must be a string")
    if not url or len(url) > 2048:
        raise ValueError("url must contain between 1 and 2048 characters")
    if any(character.isspace() for character in url):
        raise ValueError("url must not contain whitespace")
    if not url.startswith(("http://", "https://")):
        raise ValueError("url must start with http:// or https://")

    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname
        parsed.port
    except ValueError:
        raise ValueError("url is malformed") from None

    if parsed.scheme not in ("http", "https") or not hostname or parsed.netloc.endswith(":"):
        raise ValueError("url must include a valid hostname")


class URLShortener:
    """URL shortener instance configured with a hash-table backend."""

    def __init__(self, backend: str = "chaining"):
        if backend == "chaining":
            table_type = HashTable
        elif backend == "linear":
            table_type = LinearProbingHashTable
        else:
            raise ValueError("backend must be 'chaining' or 'linear'")

        self.backend = backend
        self.url_to_code = table_type()
        self.code_to_url = table_type()
        self._next_id = 0

    def shorten(self, url: str) -> str:
        """Return a stable Base62 code for a valid HTTP(S) URL."""
        _validate_url(url)

        existing_code = self.url_to_code.get(url)
        if existing_code is not None:
            return existing_code

        code = encode(self._next_id)
        self._next_id += 1
        self.url_to_code.put(url, code)
        self.code_to_url.put(code, url)
        return code

    def expand(self, code: str) -> str | None:
        """Return the original URL for a registered Base62 code."""
        if not isinstance(code, str):
            raise ValueError("code must be a Base62 string")
        decode(code)
        return self.code_to_url.get(code)


_default_shortener = URLShortener()
_url_to_code = _default_shortener.url_to_code
_code_to_url = _default_shortener.code_to_url


def shorten(url: str) -> str:
    """Shorten using the default separate-chaining backend."""
    return _default_shortener.shorten(url)


def expand(code: str) -> str | None:
    """Expand using the default separate-chaining backend."""
    return _default_shortener.expand(code)
