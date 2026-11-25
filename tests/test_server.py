import json
import threading
import unittest
from http.client import HTTPConnection
from http.server import HTTPServer

from src.server import ShortenerHandler


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.server = HTTPServer(("127.0.0.1", 0), ShortenerHandler)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server_thread.join()
        self.server.server_close()

    def request(self, method, path, body=None, headers=None):
        connection = HTTPConnection("127.0.0.1", self.server.server_port)
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        response_body = response.read()
        result = (response.status, response.headers, response_body)
        connection.close()
        return result

    def test_home_displays_url_form(self):
        status, headers, body = self.request("GET", "/")

        self.assertEqual(status, 200)
        self.assertIn("text/html", headers["Content-Type"])
        self.assertIn(b'id="shorten-form"', body)

    def test_shortens_url_and_redirects_short_link(self):
        url = "https://server-test.example/redirect"
        status, headers, body = self.request(
            "POST",
            "/shorten",
            body=json.dumps({"url": url}),
            headers={"Content-Type": "application/json"},
        )

        self.assertEqual(status, 201)
        code = json.loads(body)["code"]

        status, headers, _ = self.request("GET", f"/{code}")

        self.assertEqual(status, 302)
        self.assertEqual(headers["Location"], url)

        status, _, body = self.request("GET", f"/api/expand/{code}")

        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["url"], url)

    def test_rejects_bad_requests_and_reports_missing_codes(self):
        status, _, _ = self.request(
            "POST",
            "/shorten",
            body="{",
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(status, 400)

        status, _, _ = self.request(
            "POST",
            "/shorten",
            body=json.dumps({"url": "ftp://server-test.example"}),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(status, 400)

        status, _, _ = self.request("GET", "/zzzzzzzzzz")
        self.assertEqual(status, 404)

        status, _, _ = self.request("GET", "/api/expand/!")
        self.assertEqual(status, 400)

    def test_table_shows_chains_and_expandable_hash_details(self):
        first_url = "https://server-test.example/a"
        second_url = "https://server-test.example/q"
        codes = []
        for url in (first_url, second_url):
            _, _, body = self.request(
                "POST",
                "/shorten",
                body=json.dumps({"url": url}),
                headers={"Content-Type": "application/json"},
            )
            codes.append(json.loads(body)["code"])

        status, _, table = self.request("GET", "/table")

        self.assertEqual(status, 200)
        self.assertIn(first_url.encode(), table)
        self.assertIn(second_url.encode(), table)
        for code in codes:
            self.assertIn(f'href="/{code}"'.encode(), table)
        self.assertIn(b'class="arrow"', table)
        self.assertIn(b"<details>", table)
        self.assertIn(b"Horner hash", table)


if __name__ == "__main__":
    unittest.main()
