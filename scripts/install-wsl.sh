#!/usr/bin/env bash
# Install mdir on Ubuntu/WSL (local PC or dev machine).
set -euo pipefail

APP_DIR="${1:-$HOME/apps/mdir}"
REPO="${MDIR_REPO:-https://github.com/jsjang-1126/mdir.git}"
MARKER="# mdir terminal file explorer"

if grep -qiE 'microsoft|wsl' /proc/version 2>/dev/null; then
  echo "WSL environment detected."
else
  echo "Linux install (also works on WSL)."
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found. On WSL/Ubuntu run:" >&2
  echo "  sudo apt update && sudo apt install -y python3 python3-venv python3-pip" >&2
  exit 1
fi

if [ ! -f "$APP_DIR/pyproject.toml" ]; then
  echo "mdir source not found at $APP_DIR"
  if ! command -v git >/dev/null 2>&1; then
    echo "Install git: sudo apt install -y git" >&2
    exit 1
  fi
  echo "Cloning from $REPO ..."
  mkdir -p "$(dirname "$APP_DIR")"
  git clone "$REPO" "$APP_DIR"
fi

cd "$APP_DIR"

if ! python3 -m venv --help >/dev/null 2>&1; then
  echo "python3-venv missing. Run:" >&2
  echo "  sudo apt install -y python3-venv python3-pip" >&2
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

PATH_LINE="export PATH=\"$APP_DIR/.venv/bin:\$PATH\""

for rc in "$HOME/.bashrc" "$HOME/.profile"; do
  [ -f "$rc" ] || continue
  if ! grep -qF "$MARKER" "$rc"; then
    {
      echo ""
      echo "$MARKER"
      echo "$PATH_LINE"
    } >> "$rc"
  else
    # Update path if install dir changed (e.g. moved clone).
    if ! grep -qF "$APP_DIR/.venv/bin" "$rc"; then
      sed -i "s|^export PATH=.*mdir.*|$PATH_LINE|" "$rc" 2>/dev/null || true
    fi
  fi
done

echo ""
echo "mdir installed: $APP_DIR/.venv/bin/mdir"
echo ""
echo "Run once:  source ~/.bashrc"
echo "Then:      mdir"
echo "           mdir /mnt/c/Users"
