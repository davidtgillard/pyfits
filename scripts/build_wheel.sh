#!/usr/bin/env bash
# Build a wheel with libfits.so bundled under pyfits/_lib/.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
"$ROOT/scripts/copy_libfits.sh"
cd "$ROOT"
# Placeholder: uv_build does not bundle .so; copy into site-packages after install
# or switch to hatchling force-include when publishing wheels.
uv build "$@"
