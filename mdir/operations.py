from __future__ import annotations

import shutil
from pathlib import Path

from mdir.models import unique_destination


class OperationError(Exception):
    pass


def mkdir(path: Path, name: str) -> Path:
    name = name.strip()
    if not name:
        raise OperationError("Directory name cannot be empty.")
    target = path / name
    if target.exists():
        raise OperationError(f"Already exists: {target}")
    target.mkdir()
    return target


def rename(path: Path, new_name: str) -> Path:
    new_name = new_name.strip()
    if not new_name:
        raise OperationError("Name cannot be empty.")
    target = path.parent / new_name
    if target.exists():
        raise OperationError(f"Already exists: {target}")
    path.rename(target)
    return target


def delete(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def copy_item(source: Path, dest_dir: Path) -> Path:
    if not dest_dir.is_dir():
        raise OperationError(f"Not a directory: {dest_dir}")
    target = unique_destination(dest_dir, source.name)
    if source.is_dir():
        shutil.copytree(source, target)
    else:
        shutil.copy2(source, target)
    return target


def move_item(source: Path, dest_dir: Path) -> Path:
    if not dest_dir.is_dir():
        raise OperationError(f"Not a directory: {dest_dir}")
    target = unique_destination(dest_dir, source.name)
    shutil.move(str(source), str(target))
    return target
