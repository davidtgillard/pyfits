# pyfits

Python FITS file handling library.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) for dependency and environment management

## Development setup

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if needed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Sync the environment (includes dev tools):

```bash
uv sync --all-groups
```

## Quality checks

Run lint, type checking, and dependency auditing:

```bash
uv run ruff check . && uv run mypy && uv run pip-audit
```

Individual commands:

```bash
uv run ruff check .    # lint
uv run ruff format .   # format
uv run mypy            # typecheck
uv run pip-audit       # dependency audit
```

Format code:

```bash
uv run ruff format .
```

## Linting

Ruff is configured for linting, formatting, docstrings (`D`, `DOC`), security (`S`), naming (`N`), and pytest style (`PT`). See [docs/ruff.md](docs/ruff.md) for the full configuration reference.

## License

AGPL-3.0-or-later — see [LICENSE](LICENSE).
