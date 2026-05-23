# Usage

## Repository workflow

Open a repository session with a context manager (recommended) or call `close()` explicitly:

```python
from pathlib import Path
from pyfits import ObjectTypeName, Repo

with Repo(Path("my-product")) as repo:
    repo.init()
    repo.register_node_type("req", abstract=True)
    repo.register_node_type("REQ", extends="req")
    node_id = repo.new_node(ObjectTypeName("REQ"), title="First requirement")
    result = repo.validate()
    print(result.summary.error_count, len(result.validation_issues))
```

You can optionally open against a registry snapshot:

```python
with Repo(Path("my-product"), registry_snapshot=Path("snapshots/registry.json")) as repo:
    ...
```

See [`Repo`](api/repo.md) for all session methods.

## Response validation

Every libfits JSON response is validated before returning to callers:

1. **JSON Schema** — schemas are loaded from the embedded `FITS_*_schema()` accessors in the loaded `libfits.so` (not vendored files). Failures raise `FitsSchemaError`.
2. **Invariants** — e.g. successful `validate()` must include `validation_issues` and `summary` (the embedded `validate_response` schema only requires `ok`).

Operations without a libfits success schema (`init`, `new_link`, `remove`, `register_*`, `output_graph`) use a minimal local `ok: true` schema. `output_graph` success additionally requires a `graph` object in Python.

## Inspecting schemas

```python
from pyfits import schemas

doc = schemas.schema_dict("validate_response")
schemas.validator("error_response").validate(
    {"ok": False, "error": {"code": "x", "message": "y"}}
)
```

See the [Schemas API](api/schemas.md) reference for available helpers.
