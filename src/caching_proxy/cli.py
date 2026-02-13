from __future__ import annotations

import argparse
from urllib.parse import urlparse

from .cache import CacheStore
from .server import run_server


def is_valid_origin(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Caching proxy CLI")
    parser.add_argument("--port", type=int, help="Port for proxy server")
    parser.add_argument("--origin", type=str, help="Origin URL to forward requests to")
    parser.add_argument("--clear-cache", action="store_true", help="Clear cached responses and exit")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    cache_store = CacheStore()

    if args.clear_cache:
        cache_store.clear()
        print("Cache cleared.")
        return

    if args.port is None or args.origin is None:
        parser.error("Use --port and --origin to start server, or --clear-cache to clear cache.")

    if not is_valid_origin(args.origin):
        parser.error("--origin must be a valid http/https URL")

    run_server(args.port, args.origin, cache_store)


if __name__ == "__main__":
    main()
