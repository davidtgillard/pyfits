"""Validate libfits JSON responses."""

from __future__ import annotations

from typing import Any

import jsonschema

from pyfits._schemas import SUCCESS_SCHEMA_BY_OPERATION, validate_document
from pyfits.errors import FitsError, FitsSchemaError
from pyfits.result import Err, Ok, Result


def validate_response(operation: str, doc: dict[str, Any]) -> Result[None, FitsError]:
    """Validate a parsed JSON response for an operation.

    Args:
        operation: libfits JSON operation name (e.g. ``validate``, ``new_node``).
        doc: Parsed response object.

    Returns:
        ``Ok(None)`` when validation succeeds, or ``Err(FitsSchemaError)`` when
        validation fails.

    Raises:
        KeyError: When ``operation`` is unknown for success response validation.
    """
    if doc.get("ok") is False:
        schema_id = "error_response"
    elif operation not in SUCCESS_SCHEMA_BY_OPERATION:
        msg = f"unknown operation for response validation: {operation}"
        raise KeyError(msg)
    else:
        schema_id = SUCCESS_SCHEMA_BY_OPERATION[operation]

    match validate_document(schema_id, doc):
        case Ok(_):
            return Ok(None)
        case Err(error):
            if isinstance(error, jsonschema.ValidationError):
                msg = f"{operation} response failed schema {schema_id}: {error.message}"
                return Err(
                    FitsSchemaError(
                        msg,
                        operation=operation,
                        schema_id=schema_id,
                        validation_message=error.message,
                    )
                )
            return Err(error)
