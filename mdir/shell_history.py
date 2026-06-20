from __future__ import annotations

import json
from pathlib import Path

from mdir.bookmarks import CONFIG_DIR

HISTORY_FILE = CONFIG_DIR / "shell-history.json"
MAX_HISTORY = 30


def _ensure_config() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def _folder_key(folder: Path) -> str:
    return str(folder.expanduser().resolve())


def _load_all() -> dict[str, list[str]]:
    _ensure_config()
    if not HISTORY_FILE.exists():
        return {}
    try:
        data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(data, dict):
        return {}
    result: dict[str, list[str]] = {}
    for key, value in data.items():
        if isinstance(value, list):
            result[str(key)] = [str(item) for item in value if str(item).strip()]
    return result


def _save_all(data: dict[str, list[str]]) -> None:
    _ensure_config()
    HISTORY_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def get_history(folder: Path) -> list[str]:
    """Return commands for folder, oldest first."""
    return list(_load_all().get(_folder_key(folder), []))


def add_command(folder: Path, command: str) -> None:
    command = command.strip()
    if not command:
        return
    key = _folder_key(folder)
    data = _load_all()
    commands = data.get(key, [])
    if command in commands:
        commands.remove(command)
    commands.append(command)
    if len(commands) > MAX_HISTORY:
        commands = commands[-MAX_HISTORY:]
    data[key] = commands
    _save_all(data)


def remove_command_at(folder: Path, index: int) -> None:
    key = _folder_key(folder)
    data = _load_all()
    commands = data.get(key, [])
    if 0 <= index < len(commands):
        commands.pop(index)
        if commands:
            data[key] = commands
        else:
            data.pop(key, None)
        _save_all(data)
