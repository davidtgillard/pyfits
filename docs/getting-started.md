# Getting started

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) for dependency and environment management
- A built `libfits.so` (bundled in wheels after `scripts/copy_libfits.sh`, or from a sibling `fits` checkout)

## Development setup

Build libfits and copy the shared library into the package:

```bash
# From pyfits repo root; expects ../fits or set LIBFITS_SRC
./scripts/copy_libfits.sh
uv sync --all-groups
```

Or point at an existing build:

```bash
export PYFITS_LIB_PATH=/path/to/libfits.so
uv sync --all-groups
```

## libfits coupling

- C ABI version is read from the loaded library (`pyfits.libfits_version_packed()`, etc.).
- Pin the libfits git ref in [`.fits-lib-version`](https://github.com/davidtgillard/pyfits/blob/main/.fits-lib-version) for CI.
- CI checks out `davidtgillard/fits` and builds before tests.

## Documentation

Build and preview the docs locally:

```bash
uv sync --group docs
uv run mkdocs serve   # preview at http://127.0.0.1:8000
uv run mkdocs build --strict
```

## Quality checks

```bash
uv run ruff check . && uv run ruff format . && uv run mypy && uv run pytest && uv run pip-audit
```
