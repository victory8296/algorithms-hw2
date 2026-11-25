"""In-memory URL shortening backed by custom hash tables."""

from urllib.parse import urlsplit

from src.base62 import decode, encode
from src.hash_table import HashTable


_url_to_code = HashTable()
_code_to_url = HashTable()
_next_id = 0


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


def shorten(url: str) -> str:
    """Return a stable Base62 code for a valid HTTP(S) URL."""
    global _next_id

    _validate_url(url)

    existing_code = _url_to_code.get(url)
    if existing_code is not None:
        return existing_code

    code = encode(_next_id)
    _next_id += 1
    _url_to_code.put(url, code)
    _code_to_url.put(code, url)
    return code


def expand(code: str) -> str | None:
    """Return the original URL for a registered Base62 code."""
    if not isinstance(code, str):
        raise ValueError("code must be a Base62 string")
    decode(code)
    return _code_to_url.get(code)
