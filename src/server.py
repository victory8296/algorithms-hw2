"""HTTP interface for the in-memory URL shortener."""

import argparse
import html
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit

from src.shortener import _url_to_code, expand, shorten

MAX_REQUEST_BODY_BYTES = 1_048_576


class _JSONObject:
    def __init__(self, pairs: list[tuple[str, object]]):
        self._pairs = pairs

    def get(self, name: str) -> object | None:
        for key, value in reversed(self._pairs):
            if key == name:
                return value
        return None


class ShortenerHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if path == "/":
            self._send_html(200, _home_page())
            return
        if path == "/table":
            self._send_html(200, _table_page())
            return

        api_prefix = "/api/expand/"
        if path.startswith(api_prefix):
            self._handle_expand(path[len(api_prefix) :])
            return

        if path.startswith("/") and path.count("/") == 1:
            code = path[1:]
            try:
                url = expand(code)
            except ValueError:
                self.send_error(404, "Short URL not found")
                return
            if url is None:
                self.send_error(404, "Short URL not found")
                return

            self.send_response(302)
            self.send_header("Location", url)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        self.send_error(404, "Not found")

    def do_POST(self) -> None:
        if urlsplit(self.path).path != "/shorten":
            self.send_error(404, "Not found")
            return

        try:
            url = self._read_url()
            code = shorten(url)
        except (UnicodeDecodeError, ValueError) as error:
            self._send_json(400, _json_object("error", str(error)))
            return

        self._send_json(201, _json_object("code", code))

    def _handle_expand(self, code: str) -> None:
        try:
            url = expand(code)
        except ValueError as error:
            self._send_json(400, _json_object("error", str(error)))
            return

        if url is None:
            self.send_error(404, "Short URL not found")
            return
        self._send_json(200, _json_object("url", url))

    def _read_url(self) -> str:
        content_length = self.headers.get("Content-Length")
        if content_length is None:
            raise ValueError("Content-Length is required")
        try:
            body_length = int(content_length)
        except ValueError:
            raise ValueError("Content-Length must be an integer") from None
        if body_length < 0 or body_length > MAX_REQUEST_BODY_BYTES:
            raise ValueError("Request body size is invalid")

        try:
            payload = json.loads(
                self.rfile.read(body_length), object_pairs_hook=_JSONObject
            )
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ValueError("Request body must be valid JSON") from None

        if not isinstance(payload, _JSONObject):
            raise ValueError("Request body must be a JSON object")
        url = payload.get("url")
        if not isinstance(url, str):
            raise ValueError("url must be a string")
        return url

    def _send_json(self, status: int, body: str) -> None:
        encoded_body = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded_body)))
        self.end_headers()
        self.wfile.write(encoded_body)

    def _send_html(self, status: int, body: str) -> None:
        encoded_body = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded_body)))
        self.end_headers()
        self.wfile.write(encoded_body)


def _json_object(key: str, value: str) -> str:
    return f"{{{json.dumps(key)}:{json.dumps(value, ensure_ascii=False)}}}"


def _home_page() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>URL Shortener</title>
  <style>
    body { font: 1rem sans-serif; margin: 3rem auto; max-width: 46rem; padding: 0 1rem; }
    input { box-sizing: border-box; padding: .65rem; width: 100%; }
    button { cursor: pointer; margin-top: .75rem; padding: .6rem 1rem; }
    #result { margin-top: 1.5rem; }
    .error { color: #a11; }
  </style>
</head>
<body>
  <h1>URL Shortener</h1>
  <form id="shorten-form">
    <label for="url">URL to shorten</label>
    <input id="url" name="url" type="url" maxlength="2048" required>
    <button type="submit">Shorten</button>
  </form>
  <p id="result" aria-live="polite"></p>
  <p><a href="/table">View hash table</a></p>
  <script>
    document.getElementById("shorten-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const result = document.getElementById("result");
      result.className = "";
      result.textContent = "Shortening...";
      try {
        const response = await fetch("/shorten", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({url: document.getElementById("url").value})
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || "Could not shorten this URL.");
        }
        const link = document.createElement("a");
        link.href = "/" + encodeURIComponent(data.code);
        link.textContent = link.href;
        result.replaceChildren(document.createTextNode("Short link: "), link);
      } catch (error) {
        result.className = "error";
        result.textContent = error.message;
      }
    });
  </script>
</body>
</html>
"""


def _hash_details(key: str, capacity: int, bucket_index: int) -> str:
    steps = []
    value = 0
    for character in key:
        next_value = (31 * value + ord(character)) % capacity
        escaped_character = html.escape(repr(character))
        steps.append(
            "<li>"
            f"h = (31 × {value} + ord({escaped_character}) [{ord(character)}]) "
            f"mod {capacity} = {next_value}"
            "</li>"
        )
        value = next_value

    return (
        "<details>"
        f"<summary>Horner hash: bucket {bucket_index}</summary>"
        "<p>Start with h = 0, then apply each character from left to right:</p>"
        f"<ol>{''.join(steps)}</ol>"
        f"<p>Final bucket index: {value}</p>"
        "</details>"
    )


def _table_page() -> str:
    table = _url_to_code
    rows = []
    for bucket_index, head in enumerate(table._buckets):
        chain = []
        node = head
        while node is not None:
            key = html.escape(node.key)
            code = html.escape(node.value)
            short_link = f"/{code}"
            chain.append(
                '<section class="node">'
                f"<p><strong>URL key:</strong> <code>{key}</code></p>"
                f"<p><strong>Short code:</strong> <code>{code}</code></p>"
                f'<p><strong>Short link:</strong> <a href="{short_link}">'
                f"{short_link}</a></p>"
                f"{_hash_details(node.key, table.capacity, bucket_index)}"
                "</section>"
            )
            node = node.next

        connected_nodes = (
            '<span class="arrow" aria-label="next node">&rarr;</span>'.join(chain)
            if chain
            else "&mdash;"
        )
        rows.append(
            f"<tr><th scope=\"row\">{bucket_index}</th>"
            f"<td>{connected_nodes}</td></tr>"
        )

    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>Hash table</title>"
        "<style>"
        "body{font:1rem sans-serif;margin:2rem auto;max-width:80rem;padding:0 1rem}"
        "table{border-collapse:collapse;width:100%}"
        "th,td{border:1px solid #bbb;padding:.75rem;text-align:left;vertical-align:top}"
        "th{width:5rem}code{overflow-wrap:anywhere}.node{display:inline-block;"
        "border:1px solid #888;border-radius:.35rem;margin:.25rem;padding:.5rem;"
        "max-width:36rem}.node p{margin:.35rem 0}.arrow{font-size:1.4rem;"
        "margin:.25rem}details{margin-top:.5rem}details ol{max-height:24rem;"
        "overflow:auto}details li{font-family:monospace;font-size:.85rem}"
        "</style></head><body>"
        "<h1>Current hash table</h1>"
        '<p><a href="/">Back to URL shortener</a></p>'
        f"<p>Capacity: {table.capacity}; entries: {len(table)}</p>"
        "<table><thead><tr><th>Bucket</th><th>Chain (URL &rarr; code)</th>"
        "</tr></thead><tbody>"
        f"{''.join(rows)}"
        "</tbody></table></body></html>"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the URL shortener HTTP server.")
    parser.add_argument("--port", type=int, default=8000)
    arguments = parser.parse_args()

    with HTTPServer(("", arguments.port), ShortenerHandler) as server:
        print(f"URL shortener listening on port {arguments.port}")
        server.serve_forever()


if __name__ == "__main__":
    main()
