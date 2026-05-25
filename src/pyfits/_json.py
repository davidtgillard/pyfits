"""JSON request helpers and response handling."""

from __future__ import annotations

import json
from typing import Any, cast

from pyfits import _native
from pyfits._validate import validate_response
from pyfits.errors import FitsError, _error_from_error_document, _error_from_status
from pyfits.result import Err, Ok, Result


def _c_operation(operation: str) -> str:
    """C symbol suffix for ``FITS_{name}`` (Python ``remove`` -> ``remove_obj``)."""
    return "remove_obj" if operation == "remove" else operation


def dumps_request(payload: dict[str, Any] | None) -> bytes | None:
    """Encode a request dict as UTF-8 JSON bytes.

    Args:
        payload: Request object to serialize, or ``None`` for no request body.

    Returns:
        Compact UTF-8 JSON bytes, or ``None`` when ``payload`` is ``None``.
    """
    if payload is None:
        return None
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


def call_and_parse(
    operation: str,
    handle: Any,
    request: dict[str, Any] | None,
) -> Result[dict[str, Any], FitsError]:
    """Call a libfits JSON API operation and return the parsed response.

    Args:
        operation: libfits operation name (e.g. ``validate``, ``new_node``).
        handle: Open repository session handle.
        request: Optional request object serialized as JSON.

    Returns:
        ``Ok(parsed)`` after schema validation, or ``Err(FitsError)`` on failure.
    """
    c_op = _c_operation(operation)
    call_result = _native.call_json(c_op, handle, dumps_request(request))
    if isinstance(call_result, Err):
        return call_result
    status, text = call_result.ok_value
    if not text:
        error_result = _native.last_error()
        if isinstance(error_result, Err):
            return error_result
        err = _error_from_status(status, error_result.ok_value)
        if err is not None:
            return Err(err)
        return Ok({})
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        msg = f"{operation} returned invalid JSON: {exc}"
        return Err(FitsError(msg))
    if not isinstance(parsed, dict):
        msg = f"{operation} response must be a JSON object"
        return Err(FitsError(msg))
    validate_result = validate_response(operation, parsed)
    if isinstance(validate_result, Err):
        return validate_result
    if status != 0:
        doc_err = _error_from_error_document(parsed)
        if doc_err is not None:
            return Err(doc_err)
        error_result = _native.last_error()
        if isinstance(error_result, Err):
            return error_result
        status_err = _error_from_status(status, error_result.ok_value)
        return Err(cast(FitsError, status_err))
    doc_err = _error_from_error_document(parsed)
    if doc_err is not None:
        return Err(doc_err)
    return Ok(parsed)
