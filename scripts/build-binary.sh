#!/usr/bin/env bash
# Build a single Linux executable: dist/mdir
# No Python/pip required on the target machine (x86_64 Linux).
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -d .venv ]; then
  echo "Create .venv first. See README.md" >&2
  exit 1
fi

.venv/bin/pip install -q pyinstaller
rm -rf build dist

.venv/bin/pyinstaller mdir.spec

echo ""
echo "Built: dist/mdir ($(du -h dist/mdir | cut -f1))"
echo "Test:  ./dist/mdir --help"
echo ""
echo "Upload dist/mdir to GitHub Releases (Linux x86_64)."
