# Usage

## Repository workflow

Open a repository session with `Repo.open()` and a context manager (recommended) or call `close()` explicitly:

```python
from pathlib import Path

from pyfits import ObjectTypeName, Ok, Repo

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
        ...
```

You can optionally open against a registry snapshot:

```python
match Repo.open(Path("my-product"), registry_snapshot=Path("snapshots/registry.json")):
    case Ok(repo):
        ...
```

See [`Repo`](api/repo.md) for all session methods.

## Response validation

Every libfits JSON response is validated before returning to callers:

1. **JSON Schema** — schemas are loaded from the embedded `FITS_*_schema()` accessors in the loaded `libfits.so` (not vendored files). Failures return `Err(FitsSchemaError)`.
2. **Invariants** — e.g. successful `validate()` must include `validation_issues` and `summary` (the embedded `validate_response` schema only requires `ok`).

Operations without a libfits success schema (`init`, `new_link`, `remove`, `register_*`, `output_graph`) use a minimal local `ok: true` schema. `output_graph` success additionally requires a `graph` object in Python.

## Inspecting schemas

```python
from pyfits import Ok, schemas

match schemas.schema_dict("validate_response"):
    case Ok(doc):
        ...
match schemas.validator("error_response"):
    case Ok(v):
        v.validate({"ok": False, "error": {"code": "x", "message": "y"}})
```

See the [Schemas API](api/schemas.md) reference for available helpers.
