#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

ENV_PREFIX="${SETSCOUT_CONDA_PREFIX:-$ROOT/setscout-env}"

if [[ ! -x "$ENV_PREFIX/bin/python" ]]; then
  echo "Local Python environment not found at: $ENV_PREFIX" >&2
  echo "Create it with: conda env create -p \"$ENV_PREFIX\" -f environment.yml" >&2
  exit 1
fi

echo "Starting SetScout UI..."
echo "Project: $ROOT"
echo "Python: $ENV_PREFIX/bin/python"

exec "$ENV_PREFIX/bin/python" app.py "$@"
