# Errors

pyfits raises typed exceptions when libfits operations fail or when response JSON does not pass validation.

| Exception | Meaning |
|-----------|---------|
| `FitsError` | `ok: false` JSON response or negative C status |
| `FitsSchemaError` | Response JSON failed schema or invariant checks |

## FitsError

Raised for operational failures. When libfits returns a structured error document, `code` is set from the JSON `error.code` field. When a negative C status is returned without JSON, `status` may be set to a [`FitsStatus`](api/exceptions.md#pyfits._errors.FitsStatus) value.

## FitsSchemaError

Subclass of `FitsError` raised when a response fails JSON Schema validation or pyfits invariant checks. Attributes include `operation`, `schema_id`, and optionally `validation_message`.

See the [Exceptions API](api/exceptions.md) reference for full details.
