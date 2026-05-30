# Errors

pyfits returns operational failures as `Result[..., FitsError]` (`Ok` / `Err`) instead of raising exceptions. Programming mistakes still raise Python exceptions.

| Mechanism | Meaning |
|-----------|---------|
| `Err(FitsError)` | `ok: false` JSON response, negative C status, or missing libfits |
| `Err(FitsSchemaError)` | Response JSON failed schema or invariant checks |
| `ValueError` | Invalid caller input (e.g. `ObjectTypeName`, `Id`, `TargetId`, unknown `SchemaId`) |
| `RuntimeError` | Using `Repo` after `close()` (check :attr:`~pyfits.Repo.is_closed` first) |
| `KeyError` | Unknown operation for response validation |

## Result-based operational errors

Session and libfits methods return `Result`:

```python
match Repo.open(path):
    case Ok(repo):
        match repo.init():
            case Ok(_):
                ...
            case Err(err):
                handle(err)
    case Err(err):
        handle(err)
```

`FitsError` and `FitsSchemaError` are payload types attached to `Err`. They are not raised for normal libfits operation failures on the public `Repo` API.

## FitsError

Carried in `Err(...)` for operational failures. When libfits returns a structured error document, `code` is set from the JSON `error.code` field. When a negative C status is returned without JSON, `status` may be set to a {py:class}`FitsStatus <pyfits.errors.FitsStatus>` value.

## FitsSchemaError

Subclass of `FitsError` used when a response fails JSON Schema validation or pyfits invariant checks. Attributes include `operation`, `schema_id`, and optionally `validation_message`.

See the [Exceptions API](api/exceptions) reference for full details.

## Duplicate registration

libfits 0.4.1 adds explicit duplicate errors. `register_node_type` and
`register_link_type` are **not idempotent**: repeating the same registration
returns `Err(FitsError)` with a structured JSON error body.

| JSON `error.code` | When |
|-------------------|------|
| `DuplicateNodeType` | Re-registering a node type |
| `DuplicateLinkType` | Re-registering a link type |
| `DuplicateInstanceId` | Duplicate `target_id` at create or rename |

These map to C status `FitsStatus.ERR_ALREADY_EXISTS` (`-14`). This is distinct
from `AlreadyInitialized` / `FitsStatus.ERR_ALREADY_INITIALIZED` (`-7`), which
`init` returns when repository scaffold files already exist.

## libfits 0.4 status codes

libfits 0.4 adds stable negative statuses for nested subgraph and duplicate
operations:

| Status | Value | Meaning |
|--------|-------|---------|
| `FitsStatus.ERR_SUBGRAPH_INVALID` | -12 | Nested subgraph index or layout is invalid |
| `FitsStatus.ERR_UNKNOWN_NESTED_TYPE` | -13 | Nested type not registered for the container |
| `FitsStatus.ERR_ALREADY_EXISTS` | -14 | Duplicate node type, link type, or instance id |
