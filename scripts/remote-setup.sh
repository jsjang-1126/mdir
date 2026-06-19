#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${1:-$HOME/apps/mdir}"

cd "$APP_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required on the remote server." >&2
  exit 1
fi

if [ ! -d .venv ]; then
  python3 -m venv --without-pip .venv 2>/dev/null || python3 -m venv .venv
fi

if [ ! -x .venv/bin/pip ]; then
  if ! .venv/bin/python -m pip --version >/dev/null 2>&1; then
    tmp="$(mktemp)"
    curl -fsSL https://bootstrap.pypa.io/get-pip.py -o "$tmp"
    .venv/bin/python "$tmp"
    rm -f "$tmp"
  fi
fi

.venv/bin/pip install -q -U pip
.venv/bin/pip install -q -e .

MARKER="# mdir terminal file explorer"
LINE='export PATH="$HOME/apps/mdir/.venv/bin:$PATH"'

for rc in "$HOME/.bashrc" "$HOME/.profile"; do
  [ -f "$rc" ] || continue
  if ! grep -qF "$MARKER" "$rc"; then
    {
      echo ""
      echo "$MARKER"
      echo "$LINE"
    } >> "$rc"
  fi
done

echo "mdir installed at $APP_DIR/.venv/bin/mdir"
"$APP_DIR/.venv/bin/mdir" --help | head -3
