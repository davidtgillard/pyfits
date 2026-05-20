# pyfits

Python bindings for [libfits](https://github.com/davidtgillard/fits) — the fits graph repository engine (nodes, links, registry). This is **not** astronomy FITS file I/O (historical Astropy `pyfits`).

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

## Usage

```python
from pathlib import Path
from pyfits import Repo

with Repo(Path("my-product")) as repo:
    repo.init()
    repo.register_node_type("req", abstract=True)
    repo.register_node_type("REQ", extends="req")
    node_id = repo.new_node("REQ", title="First requirement")
    result = repo.validate()
    print(result.summary.error_count, len(result.validation_issues))
```

## Response validation

Every libfits JSON response is validated before returning to callers:

1. **JSON Schema** — schemas are loaded from the embedded `FITS_*_schema()` accessors in the loaded `libfits.so` (not vendored files). Failures raise `FitsSchemaError`.
2. **Invariants** — e.g. successful `validate()` must include `validation_issues` and `summary` (the embedded `validate_response` schema only requires `ok`).

Operations without a libfits success schema (`init`, `new_link`, `remove`, `register_*`, `output_graph`) use a minimal local `ok: true` schema. `output_graph` success additionally requires a `graph` object in Python.

Inspect schemas:

```python
from pyfits import schemas

doc = schemas.schema_dict("validate_response")
schemas.validator("error_response").validate({"ok": False, "error": {"code": "x", "message": "y"}})
```

## Errors

| Exception | Meaning |
|-----------|---------|
| `FitsError` | `ok: false` JSON response or negative C status |
| `FitsSchemaError` | Response JSON failed schema or invariant checks |

## Threading

Use one `Repo` per thread; do not share handles across threads without external locking (libfits v0 contract).

## Quality checks

```bash
uv run ruff check . && uv run ruff format . && uv run mypy && uv run pytest && uv run pip-audit
```

## libfits coupling

- C ABI version is read from the loaded library (`pyfits.api_version_packed()`, etc.).
- Pin the libfits git ref in [`.fits-lib-version`](.fits-lib-version) for CI.
- CI checks out `davidtgillard/fits` and builds before tests.

## License

AGPL-3.0-or-later — see [LICENSE](LICENSE).
