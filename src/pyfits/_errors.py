"""libfits status codes and pyfits exceptions."""

from __future__ import annotations

from enum import IntEnum
from typing import Any


class FitsStatus(IntEnum):
    """Stable libfits status codes from fits_core.h.

    Negative values are stable across releases and match ``FITS_ERR_*`` macros.
    Use :func:`status_from_int` to map raw C return values.

    Attributes:
        OK: Operation succeeded (``FITS_OK``).
        ERR_INVALID_ARGUMENT: NULL handle, bad ``struct_size``, or missing
            required field.
        ERR_REPO_NOT_FOUND: Repository root or registry snapshot path not found.
        ERR_REGISTRY: ``.fits/registry.json`` load, parse, or validation error.
        ERR_LINKS_INVALID: ``links/links.jsonc`` missing or invalid.
        ERR_SNAPSHOT_MISMATCH: Live registry differs from the snapshot fixed at
            repo open.
        ERR_UNKNOWN_ID_PREFIX: Unknown node type or object id prefix.
        ERR_ALREADY_INITIALIZED: ``init`` called on an already initialized repo.
        ERR_OUT_OF_MEMORY: Heap allocation failed inside libfits.
        ERR_IO: Filesystem I/O error.
        ERR_NOT_IMPLEMENTED: Operation not implemented in this libfits build.
        ERR_INTERNAL: Unexpected internal libfits error.
    """

    OK = 0  # Operation succeeded (FITS_OK).
    ERR_INVALID_ARGUMENT = -1  # NULL handle, bad struct_size, missing field.
    ERR_REPO_NOT_FOUND = -2  # Repo root or registry snapshot path not found.
    ERR_REGISTRY = -3  # .fits/registry.json load, parse, or validation error.
    ERR_LINKS_INVALID = -4  # links/links.jsonc missing or invalid.
    ERR_SNAPSHOT_MISMATCH = -5  # Live registry != snapshot configured at open.
    ERR_UNKNOWN_ID_PREFIX = -6  # Unknown node type or object id prefix.
    ERR_ALREADY_INITIALIZED = -7  # init on an already initialized repository.
    ERR_OUT_OF_MEMORY = -8  # Heap allocation failed.
    ERR_IO = -9  # Filesystem I/O error.
    ERR_NOT_IMPLEMENTED = -10  # Operation not implemented.
    ERR_INTERNAL = -11  # Unexpected internal error.


class FitsError(Exception):
    """libfits operation failed."""

    def __init__(
        self,
        message: str,
        *,
        status: FitsStatus | None = None,
        code: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code


class FitsSchemaError(FitsError):
    """Response JSON failed schema or invariant checks."""

    def __init__(
        self,
        message: str,
        *,
        operation: str,
        schema_id: str,
        validation_message: str | None = None,
    ) -> None:
        super().__init__(message)
        self.operation = operation
        self.schema_id = schema_id
        self.validation_message = validation_message


def status_from_int(value: int) -> FitsStatus | None:
    """Map a C FitsStatus integer to FitsStatus, or None if unknown."""
    try:
        return FitsStatus(value)
    except ValueError:
        return None


def raise_for_error_document(doc: dict[str, Any]) -> None:
    """Raise FitsError when doc is a schema-validated ``ok: false`` response."""
    if doc.get("ok") is not False:
        return
    err = doc.get("error")
    if not isinstance(err, dict):
        msg = "libfits returned ok=false without an error object"
        raise FitsError(msg, code="invalid_error_shape")
    code = err.get("code")
    message = err.get("message")
    if not isinstance(code, str) or not isinstance(message, str):
        msg = "libfits error object missing code or message"
        raise FitsError(msg, code="invalid_error_shape")
    raise FitsError(message, code=code)


def raise_for_status(status: int, last_error: str) -> None:
    """Raise FitsError for a negative C status when no JSON body was returned."""
    if status == FitsStatus.OK:
        return
    st = status_from_int(status)
    msg = last_error if last_error else f"libfits call failed with status {status}"
    raise FitsError(msg, status=st)
