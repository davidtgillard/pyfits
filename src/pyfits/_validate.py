"""Validate libfits JSON responses."""

from __future__ import annotations

from typing import Any

import jsonschema

from pyfits._errors import FitsSchemaError
from pyfits._schemas import SUCCESS_SCHEMA_BY_OPERATION, validate_document


def validate_response(operation: str, doc: dict[str, Any]) -> None:
    """Validate a parsed JSON response for an operation.

    Args:
        operation: libfits JSON operation name (e.g. ``validate``, ``new_node``).
        doc: Parsed response object.

    Raises:
        FitsSchemaError: When validation fails.
        KeyError: When ``operation`` is unknown for success response validation.
        jsonschema.ValidationError: Propagated from :func:`validate_document`
            before being wrapped in :class:`FitsSchemaError`.
    """
    if doc.get("ok") is False:
        schema_id = "error_response"
    elif operation not in SUCCESS_SCHEMA_BY_OPERATION:
        msg = f"unknown operation for response validation: {operation}"
        raise KeyError(msg)
    else:
        schema_id = SUCCESS_SCHEMA_BY_OPERATION[operation]

    try:
        validate_document(schema_id, doc)
    except jsonschema.ValidationError as exc:
        msg = f"{operation} response failed schema {schema_id}: {exc.message}"
        raise FitsSchemaError(
            msg,
            operation=operation,
            schema_id=schema_id,
            validation_message=exc.message,
        ) from exc
