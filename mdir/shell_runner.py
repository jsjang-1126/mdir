from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

MAX_OUTPUT_LINES = 3000
MAX_OUTPUT_CHARS = 256_000

_SHELL_NOISE = (
    "cannot set terminal process group",
    "no job control in this shell",
)


def format_shell_output(raw: str) -> str:
    """Trim very large command output for responsive TUI display."""
    text = raw.rstrip("\n")
    if len(text) > MAX_OUTPUT_CHARS:
        text = (
            text[:MAX_OUTPUT_CHARS]
            + f"\n\n--- output truncated at {MAX_OUTPUT_CHARS:,} characters ---"
        )
    lines = text.splitlines()
    if len(lines) > MAX_OUTPUT_LINES:
        omitted = len(lines) - MAX_OUTPUT_LINES
        text = "\n".join(lines[:MAX_OUTPUT_LINES])
        text += f"\n\n--- {omitted:,} more lines omitted ---"
    return text or "(no output)"


def _clean_shell_stderr(text: str) -> str:
    lines = [
        line
        for line in text.splitlines()
        if not any(noise in line for noise in _SHELL_NOISE)
    ]
    return "\n".join(lines).rstrip("\n")


def _shell_argv(shell: str, command: str) -> list[str]:
    """Run via setsid so an interactive shell cannot SIGSTOP mdir."""
    shell_name = Path(shell).name
    setsid = shutil.which("setsid")
    if setsid:
        if shell_name in {"bash", "zsh", "fish"}:
            return [setsid, shell, "-ic", command]
        return [setsid, shell, "-c", command]
    if shell_name == "bash":
        return [shell, "-c", command]
    return [shell, "-c", command]


def run_shell_command(folder: Path, command: str) -> tuple[int, str]:
    """Run command in folder; return exit code and combined output text."""
    shell = os.environ.get("SHELL", "/bin/bash")
    env = os.environ.copy()
    env.setdefault("NO_COLOR", "1")
    env.setdefault("CLICOLOR", "0")

    try:
        result = subprocess.run(
            _shell_argv(shell, command),
            cwd=str(folder),
            capture_output=True,
            text=True,
            errors="replace",
            stdin=subprocess.DEVNULL,
            env=env,
        )
    except OSError as exc:
        return 1, f"Failed to run command: {exc}"

    parts: list[str] = []
    if result.stdout:
        parts.append(result.stdout.rstrip("\n"))
    stderr = _clean_shell_stderr(result.stderr)
    if stderr:
        if parts:
            parts.append("")
        parts.append(stderr)

    body = format_shell_output("\n".join(parts) if parts else "(no output)")
    if result.returncode != 0:
        body += f"\n\n--- exit code {result.returncode} ---"
    return result.returncode, body
