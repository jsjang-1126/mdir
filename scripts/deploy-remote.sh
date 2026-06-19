#!/usr/bin/env bash
set -euo pipefail

REMOTE_HOST="${1:-iwin}"
REMOTE_DIR="${2:-apps/mdir}"
SOURCE_DIR="$(cd "$(dirname "$0")/.." && pwd)"

if ! ssh -o BatchMode=yes -o ConnectTimeout=10 "$REMOTE_HOST" 'echo connected' >/dev/null 2>&1; then
  echo "Cannot SSH to '$REMOTE_HOST'." >&2
  echo "Add the host to ~/.ssh/config on this machine, then retry." >&2
  exit 1
fi

echo "Deploying mdir to ${REMOTE_HOST}:~/${REMOTE_DIR} ..."

ssh "$REMOTE_HOST" "mkdir -p ~/${REMOTE_DIR}"

rsync -az --delete \
  --exclude '.venv/' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude '.git/' \
  "$SOURCE_DIR/" "${REMOTE_HOST}:~/${REMOTE_DIR}/"

ssh "$REMOTE_HOST" "bash ~/${REMOTE_DIR}/scripts/remote-setup.sh ~/${REMOTE_DIR}"

echo ""
echo "Done. Connect and run:"
echo "  ssh ${REMOTE_HOST}"
echo "  source ~/.bashrc"
echo "  mdir"
