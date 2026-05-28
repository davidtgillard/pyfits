#!/usr/bin/env bash
# Build a wheel with libfits.so bundled under pyfits/_lib/.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
python "$ROOT/scripts/fetch_libfits.py"
cd "$ROOT"
uv build --wheel "$@"
