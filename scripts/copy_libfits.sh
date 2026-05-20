#!/usr/bin/env bash
# Build libfits and copy the shared library into pyfits for local dev / wheels.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LIBFITS_SRC="${LIBFITS_SRC:-$(cd "$ROOT/../fits" 2>/dev/null && pwd || true)}"
if [[ -z "${LIBFITS_SRC}" || ! -f "${LIBFITS_SRC}/build.zig" ]]; then
  echo "Set LIBFITS_SRC to the fits repository root" >&2
  exit 1
fi
cd "$LIBFITS_SRC"
zig build -Doptimize=ReleaseSafe
DEST="$ROOT/src/pyfits/_lib"
mkdir -p "$DEST"
cp zig-out/lib/libfits.so "$DEST/"
echo "Copied libfits.so to $DEST"
