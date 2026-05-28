# pyfits

Python bindings for [libfits](https://github.com/davidtgillard/fits) — the fits graph repository engine (nodes, links, registry). This is **not** astronomy FITS file I/O (historical Astropy `pyfits`).

## Documentation

Full API reference and guides: https://davidtgillard.github.io/pyfits/

Build locally:

```bash
uv sync --group docs
uv run sphinx-autobuild docs docs/_build/html   # preview at http://127.0.0.1:8000
uv run sphinx-build -b html -W -n docs docs/_build/html
```

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) for dependency and environment management
- **Linux x86_64** (including WSL2): `libfits.so` is downloaded from the [libfits `dev` release](https://github.com/davidtgillard/fits/releases) (see `[tool.pyfits.libfits]` in `pyproject.toml`)

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

## Usage

```python
from pathlib import Path

from pyfits import Err, ObjectTypeName, Ok, Repo

match Repo.open(Path("my-product")):
    case Ok(repo):
        with repo:
            repo.init()
            repo.register_node_type("req", abstract=True)
            repo.register_node_type("REQ", extends="req")
            match repo.new_node(ObjectTypeName("REQ"), title="First requirement"):
                case Ok(node_id):
                    match repo.validate():
                        case Ok(result):
                            print(result.summary.error_count, len(result.validation_issues))
    case Err(err):
        print(err)
```

Operational failures return `Result[..., FitsError]` (`Ok` / `Err`). Check the variant instead of catching `FitsError` for libfits operations.

Override the default `nodes/` and `links/` graph roots at init time; libfits writes the values to `.fits/fits_config.toml` under `[paths]`:

```python
repo.init(nodes_root="a/b/my_nodes", links_root="a/b/my_links")
```

## Response validation

Every libfits JSON response is validated before returning to callers:

1. **JSON Schema** — schemas are loaded from the embedded `FITS_*_schema()` accessors in the loaded `libfits.so` (not vendored files). Failures become `Err(FitsSchemaError)`.
2. **Invariants** — e.g. successful `validate()` must include `validation_issues` and `summary` (the embedded `validate_response` schema only requires `ok`).

Operations without a libfits success schema (`init`, `new_link`, `remove`, `register_*`, `output_graph`) use a minimal local `ok: true` schema. `output_graph` success additionally requires a `graph` object in Python.

Inspect schemas:

```python
from pyfits import Ok, schemas

match schemas.schema_dict(schemas.SchemaId.VALIDATE_RESPONSE):
    case Ok(doc):
        ...
match schemas.validator(schemas.SchemaId.ERROR_RESPONSE):
    case Ok(v):
        v.validate({"ok": False, "error": {"code": "x", "message": "y"}})
```

## Errors

| Mechanism | Meaning |
|-----------|---------|
| `Result[..., FitsError]` | Operational libfits failures (`ok: false`, I/O, missing lib, schema/invariant failures) |
| `ValueError` | Invalid `ObjectTypeName`, unknown `SchemaId`, or other caller input |
| `RuntimeError` | Using a `Repo` after `close()` |
| `KeyError` | Unknown operation for response validation |

`FitsError` and `FitsSchemaError` are error **payload** types carried in `Err(...)`, not control-flow exceptions on the public `Repo` API.

## Threading

Use one `Repo` per thread; do not share handles across threads without external locking (libfits v0 contract).

## Quality checks

```bash
uv run ruff check . && uv run ruff format . && uv run basedpyright && uv run mypy && uv run pytest && uv run pip-audit --skip-editable
```

## libfits coupling

- C ABI version is read from the loaded library (`pyfits.get_version()`).
- Pin the libfits GitHub release in [`pyproject.toml`](pyproject.toml) (`[tool.pyfits.libfits]`); sha256 is verified via `manifest.json` on each fetch.
- [`.fits-lib-version`](.fits-lib-version) documents the upstream git ref for cross-checking `manifest.json`’s `git_commit`.

## License

AGPL-3.0-or-later — see [LICENSE](LICENSE).
