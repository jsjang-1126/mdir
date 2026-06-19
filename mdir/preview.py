from __future__ import annotations

from pathlib import Path

from rich.syntax import Syntax
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static

PREVIEW_LIMIT = 200_000
TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".py",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".sh",
    ".bash",
    ".zsh",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".html",
    ".css",
    ".scss",
    ".xml",
    ".csv",
    ".log",
    ".ini",
    ".cfg",
    ".conf",
    ".env",
    ".rs",
    ".go",
    ".c",
    ".h",
    ".cpp",
    ".java",
    ".rb",
    ".php",
}


def is_text_file(path: Path) -> bool:
    if not path.is_file():
        return False
    if path.suffix.lower() in TEXT_EXTENSIONS:
        return True
    return _looks_text(path)


class PreviewPane(Vertical):
    DEFAULT_CSS = """
    PreviewPane {
        height: 1fr;
        min-height: 8;
        border: solid $accent-darken-2;
        padding: 0 1;
    }

    PreviewPane.hidden {
        display: none;
    }

    PreviewPane > .preview-title {
        height: 1;
        color: $text-muted;
        text-style: bold;
    }

    PreviewPane Static {
        height: 1fr;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._visible = True

    def compose(self) -> ComposeResult:
        yield Static("Preview", classes="preview-title")
        yield Static("Select a file to preview.", id="preview-body")

    def toggle(self) -> bool:
        self._visible = not self._visible
        self.set_class(not self._visible, "hidden")
        return self._visible

    def show_path(self, path: Path | None) -> None:
        title = self.query_one(".preview-title", Static)
        body = self.query_one("#preview-body", Static)

        if path is None:
            title.update("Preview")
            body.update("Select a file to preview.")
            return

        if path.is_dir():
            title.update(f"Preview — {path.name}/")
            try:
                count = sum(1 for _ in path.iterdir())
            except OSError as exc:
                body.update(f"Cannot read directory: {exc}")
                return
            body.update(f"Directory\n\nItems: {count}\nPath: {path}")
            return

        title.update(f"Preview — {path.name}")
        if path.suffix.lower() not in TEXT_EXTENSIONS and not _looks_text(path):
            try:
                size = path.stat().st_size
            except OSError:
                size = 0
            body.update(f"Binary or unsupported file\n\nSize: {size:,} bytes\nPath: {path}")
            return

        try:
            data = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            body.update(f"Cannot read file: {exc}")
            return

        truncated = len(data) > PREVIEW_LIMIT
        if truncated:
            data = data[:PREVIEW_LIMIT] + "\n\n… truncated …"

        lexer = _lexer_for(path)
        rendered = Syntax(data, lexer, theme="monokai", line_numbers=True, word_wrap=True)
        body.update(rendered)


def _looks_text(path: Path) -> bool:
    try:
        chunk = path.read_bytes()[:4096]
    except OSError:
        return False
    if not chunk:
        return True
    if b"\0" in chunk:
        return False
    return True


def _lexer_for(path: Path) -> str:
    mapping = {
        ".py": "python",
        ".md": "markdown",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".sh": "bash",
        ".bash": "bash",
        ".zsh": "bash",
        ".js": "javascript",
        ".ts": "typescript",
        ".html": "html",
        ".css": "css",
        ".xml": "xml",
        ".rs": "rust",
        ".go": "go",
        ".java": "java",
        ".rb": "ruby",
        ".php": "php",
    }
    return mapping.get(path.suffix.lower(), "text")
