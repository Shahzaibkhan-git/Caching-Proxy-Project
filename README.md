# Project Page URL
https://roadmap.sh/projects/caching-server

# Caching Proxy (Python)

A CLI tool that starts a caching proxy server.  
It forwards requests to an origin server and caches responses for repeated requests.

## Architecture and Flow

- Full project walkthrough: [`PROJECT_FLOW.md`](PROJECT_FLOW.md)

## Features

- Start proxy server on a custom port
- Forward requests to a configured origin URL
- Cache `GET` responses
- Return cache status header:
  - `X-Cache: MISS` when response comes from origin
  - `X-Cache: HIT` when response comes from cache
- Clear all cached responses with CLI flag

## Requirements

- Python 3.9+

## Project Structure

```text
.
├── pyproject.toml
├── README.md
└── src/
    └── caching_proxy/
        ├── __init__.py
        ├── cache.py
        ├── cli.py
        └── server.py
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -e .
```

## Usage

### Start proxy server

```bash
caching-proxy --port 3000 --origin http://dummyjson.com
```

This runs proxy at `http://localhost:3000` and forwards to `http://dummyjson.com`.

### Example request flow

Request:

```bash
curl -i http://localhost:3000/products
```

First call:

- Forwarded to origin
- Returns `X-Cache: MISS`

Second call to same URL:

- Served from cache
- Returns `X-Cache: HIT`

### Clear cache

```bash
caching-proxy --clear-cache
```

## CLI Options

```text
--port <number>      Port to run proxy server
--origin <url>       Origin URL to forward requests to (http/https)
--clear-cache        Clear cache and exit
```

## Notes

- Cache keys are based on request method + full target URL.
- Current implementation caches `GET` requests only.
- Cache files are stored under:
  - `$XDG_CACHE_HOME/caching-proxy` if `XDG_CACHE_HOME` is set
  - otherwise `~/.cache/caching-proxy`

## Troubleshooting

- If `pip install -e .` says no Python project found:
  - Make sure file is named `pyproject.toml` (not `.pyproject.toml`).
- If install fails due to no internet:
  - Your environment cannot download build tools from PyPI; use a network-enabled environment or preinstall required packages.
