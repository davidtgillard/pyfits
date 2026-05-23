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
    """libfits operation failed.

    Attributes:
        status: Stable C status code when no JSON error body was returned.
        code: Machine-readable error code from an ``ok: false`` JSON response.
    """

    def __init__(
        self,
        message: str,
        *,
        status: FitsStatus | None = None,
        code: str | None = None,
    ) -> None:
        """Initialize FitsError.

        Args:
            message: Human-readable error description.
            status: Optional libfits C status when raised from a negative return
                code without JSON.
            code: Optional error code from a structured JSON error response.
        """
        super().__init__(message)
        self.status = status
        self.code = code


class FitsSchemaError(FitsError):
    """Response JSON failed schema or invariant checks.

    Attributes:
        operation: libfits operation name (e.g. ``validate``).
        schema_id: Schema or invariant identifier that failed.
        validation_message: Optional detail from jsonschema when applicable.
    """

    def __init__(
        self,
        message: str,
        *,
        operation: str,
        schema_id: str,
        validation_message: str | None = None,
    ) -> None:
        """Initialize FitsSchemaError.

        Args:
            message: Human-readable error description.
            operation: libfits operation that produced the response.
            schema_id: Schema or invariant identifier that failed validation.
            validation_message: Optional jsonschema validation detail.
        """
        super().__init__(message)
        self.operation = operation
        self.schema_id = schema_id
        self.validation_message = validation_message


def lib_not_found_error(message: str) -> FitsError:
    """Build a :class:`FitsError` for a missing libfits shared library.

    Args:
        message: Human-readable error description.

    Returns:
        Error payload with ``code="lib_not_found"``.
    """
    return FitsError(message, code="lib_not_found")


def status_from_int(value: int) -> FitsStatus | None:
    """Map a C status integer to :class:`FitsStatus`.

    Args:
        value: Raw status code returned by libfits.

    Returns:
        Matching :class:`FitsStatus` member, or ``None`` when ``value`` is not
        a known status code.
    """
    try:
        return FitsStatus(value)
    except ValueError:
        return None


def error_from_error_document(doc: dict[str, Any]) -> FitsError | None:
    """Return an error for a schema-validated ``ok: false`` response.

    Args:
        doc: Parsed libfits JSON response object.

    Returns:
        :class:`FitsError` when ``doc`` has ``ok: false``; otherwise ``None``.
    """
    if doc.get("ok") is not False:
        return None
    err = doc.get("error")
    if not isinstance(err, dict):
        msg = "libfits returned ok=false without an error object"
        return FitsError(msg, code="invalid_error_shape")
    code = err.get("code")
    message = err.get("message")
    if not isinstance(code, str) or not isinstance(message, str):
        msg = "libfits error object missing code or message"
        return FitsError(msg, code="invalid_error_shape")
    return FitsError(message, code=code)


def error_from_status(status: int, last_error: str) -> FitsError | None:
    """Return an error for a negative C status without a JSON body.

    Args:
        status: Raw status code returned by libfits.
        last_error: Thread-local diagnostic string from :func:`last_error`.

    Returns:
        :class:`FitsError` when ``status`` is not :attr:`FitsStatus.OK`; otherwise
        ``None``.
    """
    if status == FitsStatus.OK:
        return None
    st = status_from_int(status)
    msg = last_error if last_error else f"libfits call failed with status {status}"
    return FitsError(msg, status=st)
