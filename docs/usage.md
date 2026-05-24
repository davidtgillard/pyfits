# Usage

## Repository workflow

Open a repository session with `Repo.open()` and a context manager (recommended) or call `close()` explicitly. While a session is open, `repo.is_closed` is `False`; after `close()` it is `True` (a closed session cannot be reopened—call `Repo.open()` again for a new session).

```python
from pathlib import Path

from pyfits import Id, ObjectTypeName, Ok, Repo, TargetId

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

### Explicit target ids and nested create

Use `TargetId` when requesting a specific single-segment id at create time (serialized to libfits as `target_id`). libfits returns canonical `Id` values:

```python
match repo.new_node(ObjectTypeName("REQ"), target_id=TargetId("login-flow")):
    case Ok(node_id):
        assert node_id == Id("login-flow")

match repo.new_node(
    ObjectTypeName("section"),
    container_id=Id("REQ-1"),
    target_id=TargetId("overview"),
):
    case Ok(nested_id):
        assert nested_id == Id("REQ-1/overview")
```

You can optionally open against a registry snapshot:

```python
match Repo.open(Path("my-product"), registry_snapshot=Path("snapshots/registry.json")):
    case Ok(repo):
        ...
```

See [`Repo`](api/repo) for all session methods.

## Response validation

Every libfits JSON response is validated before returning to callers:

1. **JSON Schema** — schemas are loaded from the embedded `FITS_*_schema()` accessors in the loaded `libfits.so` (not vendored files). Failures return `Err(FitsSchemaError)`.
2. **Invariants** — e.g. successful `validate()` must include `validation_issues` and `summary` (the embedded `validate_response` schema only requires `ok`).

Operations without a dedicated libfits success schema (`init`, `remove`, `register_*`, nested register aliases) use a minimal local `ok: true` schema. `output_graph` success is validated locally and parsed into a typed `Graph`.

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

See the [Schemas API](api/schemas) reference for available helpers.
