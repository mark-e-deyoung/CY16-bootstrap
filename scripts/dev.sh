#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

if command -v python3 >/dev/null 2>&1; then
    exec python3 "$SCRIPT_DIR/dev.py" "$@"
elif command -v python >/dev/null 2>&1; then
    exec python "$SCRIPT_DIR/dev.py" "$@"
else
    echo "Python 3 is required. Install Python and rerun this command." >&2
    exit 2
fi
