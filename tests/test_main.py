import http.server
import socketserver
import threading
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

import pytest

from trn import get_input_data, is_file, is_url

TESTS_DIR = Path(__file__).parent


class TestMultipleFiles:
    def test_multiple_files_detected(self):
        file1 = TESTS_DIR / "file1.png"
        file2 = TESTS_DIR / "file2.png"
        args = Namespace(text=[str(file1), str(file2)])

        text, files = get_input_data(args)

        assert text is None
        assert len(files) == 2
        assert files[0] == file1
        assert files[1] == file2

    def test_nonexistent_file_errors(self):
        file1 = TESTS_DIR / "file1.png"
        args = Namespace(text=[str(file1), "nonexistent.png"])

        with pytest.raises(SystemExit):
            get_input_data(args)


class SimpleHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, directory=None, **kwargs):
        self.pages = {
            "/page1": "<html><body>Page One Content</body></html>",
            "/page2": "<html><body>Page Two Content</body></html>",
        }
        super().__init__(*args, directory=directory, **kwargs)

    def do_GET(self):
        if self.path in self.pages:
            content = self.pages[self.path].encode()
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.send_header("Content-Length", len(content))
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        pass  # Suppress logging


@pytest.fixture
def test_server():
    httpd = socketserver.TCPServer(("127.0.0.1", 0), SimpleHandler)
    httpd.allow_reuse_address = True
    port = httpd.server_address[1]

    def serve():
        httpd.handle_request()
        httpd.handle_request()

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    httpd.server_close()


class TestMultipleURLs:
    def test_multiple_urls_detected(self, test_server):
        url1 = f"{test_server}/page1"
        url2 = f"{test_server}/page2"
        args = Namespace(text=[url1, url2])

        text, files = get_input_data(args)

        assert files == []
        assert "Page One Content" in text
        assert "Page Two Content" in text

    def test_mixed_url_and_nonurl_errors(self, test_server):
        url1 = f"{test_server}/page1"
        args = Namespace(text=[url1, "not a url"])

        with pytest.raises(SystemExit):
            get_input_data(args)
