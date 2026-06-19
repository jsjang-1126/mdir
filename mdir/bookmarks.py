from __future__ import annotations

import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "mdir"
BOOKMARKS_FILE = CONFIG_DIR / "bookmarks.json"


def _ensure_config() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_bookmarks() -> dict[str, str]:
    _ensure_config()
    if not BOOKMARKS_FILE.exists():
        return {}
    try:
        data = json.loads(BOOKMARKS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(k): str(v) for k, v in data.items()}


def save_bookmarks(bookmarks: dict[str, str]) -> None:
    _ensure_config()
    BOOKMARKS_FILE.write_text(
        json.dumps(bookmarks, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def add_bookmark(name: str, path: str) -> None:
    bookmarks = load_bookmarks()
    bookmarks[name] = path
    save_bookmarks(bookmarks)


def remove_bookmark(name: str) -> None:
    bookmarks = load_bookmarks()
    bookmarks.pop(name, None)
    save_bookmarks(bookmarks)
