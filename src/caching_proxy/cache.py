from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_CACHE_DIR = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "caching-proxy"


@dataclass
class CachedResponse:
    status: int
    reason: str
    headers: list[tuple[str, str]]
    body: bytes


class CacheStore:
    def __init__(self, cache_dir: Path | None = None) -> None:
        self.cache_dir = cache_dir or DEFAULT_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _make_key(method: str, url: str) -> str:
        raw = f"{method.upper()}|{url}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def _path_for_key(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def get(self, method: str, url: str) -> CachedResponse | None:
        key = self._make_key(method, url)
        file_path = self._path_for_key(key)
        if not file_path.exists():
            return None

        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
            return CachedResponse(
                status=int(payload["status"]),
                reason=str(payload["reason"]),
                headers=[(k, v) for k, v in payload["headers"]],
                body=base64.b64decode(payload["body"]),
            )
        except Exception:
            return None

    def set(
        self,
        method: str,
        url: str,
        status: int,
        reason: str,
        headers: Iterable[tuple[str, str]],
        body: bytes,
    ) -> None:
        key = self._make_key(method, url)
        file_path = self._path_for_key(key)
        payload = {
            "status": status,
            "reason": reason,
            "headers": list(headers),
            "body": base64.b64encode(body).decode("ascii"),
        }
        file_path.write_text(json.dumps(payload), encoding="utf-8")

    def clear(self) -> None:
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
