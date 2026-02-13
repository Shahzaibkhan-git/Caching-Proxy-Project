from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib import error, parse, request

from .cache import CacheStore

HOP_BY_HOP_HEADERS = {
    "connection",
    "proxy-connection",
    "keep-alive",
    "transfer-encoding",
    "te",
    "trailer",
    "upgrade",
}


def build_target_url(origin: str, incoming_path: str) -> str:
    if incoming_path.startswith("http://") or incoming_path.startswith("https://"):
        return incoming_path
    return parse.urljoin(origin.rstrip("/") + "/", incoming_path.lstrip("/"))


class CachingProxyHandler(BaseHTTPRequestHandler):
    origin = ""
    cache_store: CacheStore

    def do_GET(self) -> None:
        self._handle_request(cacheable=True)

    def do_POST(self) -> None:
        self._handle_request(cacheable=False)

    def do_PUT(self) -> None:
        self._handle_request(cacheable=False)

    def do_PATCH(self) -> None:
        self._handle_request(cacheable=False)

    def do_DELETE(self) -> None:
        self._handle_request(cacheable=False)

    def do_HEAD(self) -> None:
        self._handle_request(cacheable=False)

    def _handle_request(self, cacheable: bool) -> None:
        target_url = build_target_url(self.origin, self.path)

        if cacheable:
            cached = self.cache_store.get(self.command, target_url)
            if cached is not None:
                self._send_response(cached.status, cached.reason, cached.headers, cached.body, "HIT")
                return

        status, reason, headers, body = self._forward(target_url)

        if cacheable:
            self.cache_store.set(self.command, target_url, status, reason, headers, body)

        self._send_response(status, reason, headers, body, "MISS")

    def _forward(self, target_url: str) -> tuple[int, str, list[tuple[str, str]], bytes]:
        content_length = int(self.headers.get("Content-Length", "0") or "0")
        request_body = self.rfile.read(content_length) if content_length > 0 else None

        upstream_request = request.Request(target_url, data=request_body, method=self.command)

        for key, value in self.headers.items():
            key_lower = key.lower()
            if key_lower == "host" or key_lower in HOP_BY_HOP_HEADERS:
                continue
            upstream_request.add_header(key, value)

        try:
            with request.urlopen(upstream_request, timeout=30) as resp:
                return resp.status, str(resp.reason), list(resp.getheaders()), resp.read()
        except error.HTTPError as exc:
            return exc.code, str(exc.reason), list(exc.headers.items()), exc.read()

    def _send_response(
        self,
        status: int,
        reason: str,
        headers: list[tuple[str, str]],
        body: bytes,
        cache_status: str,
    ) -> None:
        self.send_response(status, reason)

        for key, value in headers:
            key_lower = key.lower()
            if key_lower in HOP_BY_HOP_HEADERS or key_lower == "content-length":
                continue
            self.send_header(key, value)

        self.send_header("X-Cache", cache_status)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()

        if body:
            self.wfile.write(body)


def run_server(port: int, origin: str, cache_store: CacheStore) -> None:
    handler_cls = type("ConfiguredCachingProxyHandler", (CachingProxyHandler,), {})
    handler_cls.origin = origin
    handler_cls.cache_store = cache_store

    server = ThreadingHTTPServer(("0.0.0.0", port), handler_cls)
    print(f"Caching proxy listening on http://localhost:{port} -> {origin}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down proxy server.")
    finally:
        server.server_close()
