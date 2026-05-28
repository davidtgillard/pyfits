# Getting started

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) for dependency and environment management
- **Linux x86_64** (including WSL2): `libfits.so` from the [libfits `dev` release](https://github.com/davidtgillard/fits/releases) (configured in `pyproject.toml` under `[tool.pyfits.libfits]`)

## Development setup

```bash
uv sync --all-groups
uv run python scripts/fetch_libfits.py   # optional; pytest fetches automatically
```

Or point at an existing shared library:

```bash
export PYFITS_LIB_PATH=/path/to/libfits.so
uv sync --all-groups
```

## libfits coupling

- C ABI version is read from the loaded library (`pyfits.get_version()`).
- Pin the libfits GitHub release in `pyproject.toml` (`[tool.pyfits.libfits]`); sha256 is verified via `manifest.json` on each fetch.
- [`.fits-lib-version`](https://github.com/davidtgillard/pyfits/blob/main/.fits-lib-version) documents the upstream git ref for cross-checking `manifest.json`’s `git_commit`.

## Documentation

Build and preview the docs locally:

```bash
uv sync --group docs
uv run python scripts/fetch_libfits.py
uv run sphinx-autobuild docs docs/_build/html   # preview at http://127.0.0.1:8000
uv run sphinx-build -b html -W -n docs docs/_build/html
```

## Quality checks

```bash
./local-checks.sh
```

Or run the same steps manually:

```bash
uv run python scripts/fetch_libfits.py
uv run ruff check . && uv run ruff format . && uv run basedpyright && uv run mypy && uv run pytest && uv run pip-audit --skip-editable
```
