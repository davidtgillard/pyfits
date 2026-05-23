# Errors

pyfits returns operational failures as `Result[..., FitsError]` (`Ok` / `Err`) instead of raising exceptions. Programming mistakes still raise Python exceptions.

| Mechanism | Meaning |
|-----------|---------|
| `Err(FitsError)` | `ok: false` JSON response, negative C status, or missing libfits |
| `Err(FitsSchemaError)` | Response JSON failed schema or invariant checks |
| `ValueError` | Invalid caller input (e.g. `ObjectTypeName`) |
| `RuntimeError` | Using `Repo` after `close()` |
| `KeyError` | Invalid `schemas.schema_dict` id |

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

Carried in `Err(...)` for operational failures. When libfits returns a structured error document, `code` is set from the JSON `error.code` field. When a negative C status is returned without JSON, `status` may be set to a [`FitsStatus`](api/exceptions.md#pyfits._errors.FitsStatus) value.

## FitsSchemaError

Subclass of `FitsError` used when a response fails JSON Schema validation or pyfits invariant checks. Attributes include `operation`, `schema_id`, and optionally `validation_message`.

See the [Exceptions API](api/exceptions.md) reference for full details.
