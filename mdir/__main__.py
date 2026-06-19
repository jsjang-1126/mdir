from __future__ import annotations

import argparse
from pathlib import Path

from mdir.app import run


def main() -> None:
    parser = argparse.ArgumentParser(description="mdir — terminal file explorer")
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Starting directory for both panels (default: current directory)",
    )
    args = parser.parse_args()
    start = Path(args.path).expanduser().resolve()
    if not start.is_dir():
        raise SystemExit(f"Not a directory: {start}")
    run(start)


if __name__ == "__main__":
    main()
