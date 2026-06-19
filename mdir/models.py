from __future__ import annotations

import stat
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True, slots=True)
class FileEntry:
    path: Path
    name: str
    is_dir: bool
    size: int
    modified: float
    mode: int

    @classmethod
    def from_path(cls, path: Path) -> FileEntry:
        try:
            st = path.lstat()
        except OSError:
            return cls(
                path=path,
                name=path.name,
                is_dir=False,
                size=0,
                modified=0.0,
                mode=0,
            )
        return cls(
            path=path,
            name=path.name,
            is_dir=stat.S_ISDIR(st.st_mode),
            size=st.st_size,
            modified=st.st_mtime,
            mode=st.st_mode,
        )

    @property
    def icon(self) -> str:
        if self.name == "..":
            return "⬆"
        return "📁" if self.is_dir else "📄"

    @property
    def size_text(self) -> str:
        if self.is_dir and self.name != "..":
            return "<DIR>"
        return format_size(self.size)

    @property
    def modified_text(self) -> str:
        if not self.modified:
            return "—"
        return datetime.fromtimestamp(self.modified).strftime("%Y-%m-%d %H:%M")

    @property
    def modified_detail_text(self) -> str:
        if not self.modified:
            return "—"
        return datetime.fromtimestamp(self.modified).strftime("%Y-%m-%d %H:%M:%S")

    @property
    def perm_text(self) -> str:
        if not self.mode:
            return "??????????"
        return stat.filemode(self.mode)


def format_size(num: int) -> str:
    if num < 1024:
        return f"{num} B"
    for unit in ("KB", "MB", "GB", "TB"):
        num /= 1024
        if num < 1024:
            return f"{num:.1f} {unit}"
    return f"{num:.1f} PB"


def list_directory(directory: Path) -> list[FileEntry]:
    entries: list[FileEntry] = []
    if directory.parent != directory:
        entries.append(
            FileEntry(
                path=directory.parent,
                name="..",
                is_dir=True,
                size=0,
                modified=0.0,
                mode=stat.S_IFDIR | 0o755,
            )
        )

    try:
        children = sorted(directory.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except PermissionError:
        return entries

    for child in children:
        try:
            entries.append(FileEntry.from_path(child))
        except OSError:
            continue
    return entries


def unique_destination(dest_dir: Path, name: str) -> Path:
    target = dest_dir / name
    if not target.exists():
        return target
    stem = Path(name).stem
    suffix = Path(name).suffix
    counter = 1
    while True:
        candidate = dest_dir / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1
