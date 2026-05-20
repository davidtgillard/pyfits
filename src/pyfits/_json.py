"""JSON request helpers and response handling."""

from __future__ import annotations

import json
from typing import Any

from pyfits import _native
from pyfits._errors import FitsError, raise_for_error_document, raise_for_status
from pyfits._validate import validate_response


def _c_operation(operation: str) -> str:
    """C symbol suffix for ``FITS_{name}`` (Python ``remove`` -> ``remove_obj``)."""
    return "remove_obj" if operation == "remove" else operation


def dumps_request(payload: dict[str, Any] | None) -> bytes | None:
    """Encode a request dict as UTF-8 JSON bytes."""
    if payload is None:
        return None
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


def call_and_parse(
    operation: str,
    handle: Any,
    request: dict[str, Any] | None,
) -> dict[str, Any]:
    """Call libfits JSON API, validate response, return parsed dict.

    Raises:
        FitsError: On negative status or ``ok: false`` response.
        FitsSchemaError: When response JSON fails schema validation.
    """
    c_op = _c_operation(operation)
    status, text = _native.call_json(c_op, handle, dumps_request(request))
    if not text:
        raise_for_status(status, _native.last_error())
        return {}
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        msg = f"{operation} returned invalid JSON: {exc}"
        raise FitsError(msg) from exc
    if not isinstance(parsed, dict):
        msg = f"{operation} response must be a JSON object"
        raise FitsError(msg)
    validate_response(operation, parsed)
    if status != 0:
        raise_for_error_document(parsed)
        raise_for_status(status, _native.last_error())
    raise_for_error_document(parsed)
    return parsed
