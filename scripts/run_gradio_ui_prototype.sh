#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${SETSCOUT_PROTOTYPE_PORT:-4173}"

echo "SetScout throwaway UI prototype: http://127.0.0.1:${PORT}/"
exec python3 -m http.server "$PORT" --directory "$ROOT/prototypes/gradio-ui-execution"
