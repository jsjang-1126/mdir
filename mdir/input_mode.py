from __future__ import annotations

import os
import shutil
import subprocess

# IBus (Ubuntu + ibus-hangul)
IBUS_ENGLISH_ENGINES = (
    "xkb:us::eng",
    "xkb:us:euro:eng",
    "xkb:us:intl:eng",
)

IBUS_KOREAN_MARKERS = ("hangul", "korean", "ko:", "kr:")

_FCITX5_ENGLISH = ("keyboard-us", "fcitx-keyboard-us")
_FCITX4_ENGLISH = ("fcitx-keyboard-us", "keyboard-us")


def _run(cmd: list[str], *, timeout: float = 2.0) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=os.environ.copy(),
            errors="replace",
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def _current_ibus_engine() -> str | None:
    ibus = shutil.which("ibus")
    if not ibus:
        return None
    result = _run([ibus, "engine"], timeout=1.5)
    if result is None or result.returncode != 0:
        return None
    engine = result.stdout.strip()
    return engine or None


def _is_english_engine(engine: str | None) -> bool:
    if not engine:
        return False
    lower = engine.lower()
    if any(marker in lower for marker in IBUS_KOREAN_MARKERS):
        return False
    return lower.startswith("xkb:us") or "::eng" in lower or lower == "english"


def _switch_ibus(engine: str) -> bool:
    ibus = shutil.which("ibus")
    if not ibus:
        return False
    result = _run([ibus, "engine", engine], timeout=1.5)
    if result is None or result.returncode != 0:
        return False
    return _current_ibus_engine() == engine


def _switch_ibus_english() -> bool:
    current = _current_ibus_engine()
    if _is_english_engine(current):
        return True
    for engine in IBUS_ENGLISH_ENGINES:
        if _switch_ibus(engine):
            return True
    return False


def _switch_fcitx5_english() -> bool:
    remote = shutil.which("fcitx5-remote")
    if not remote:
        return False
    for name in _FCITX5_ENGLISH:
        result = _run([remote, "-s", name], timeout=1.5)
        if result is not None and result.returncode == 0:
            return True
    result = _run([remote, "-c"], timeout=1.5)
    return result is not None and result.returncode == 0


def _switch_fcitx4_english() -> bool:
    remote = shutil.which("fcitx-remote")
    if not remote:
        return False
    for name in _FCITX4_ENGLISH:
        result = _run([remote, "-s", name], timeout=1.5)
        if result is not None and result.returncode == 0:
            return True
    result = _run([remote, "-c"], timeout=1.5)
    return result is not None and result.returncode == 0


def switch_to_english_input() -> None:
    """Switch IME to English/Latin for TUI key bindings (best effort)."""
    if _switch_ibus_english():
        return
    if _switch_fcitx5_english():
        return
    _switch_fcitx4_english()


def restore_input_mode() -> None:
    """No-op: restoring the previous IME often flipped back to Korean after mdir."""

