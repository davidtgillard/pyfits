"""Load and cache JSON Schemas embedded in libfits.

Constants:

    OK_TRUE_SCHEMA:
        pyfits-local minimal success schema when libfits has no response schema.

    OUTPUT_GRAPH_SUCCESS_SCHEMA:
        pyfits-local success schema for ``output_graph`` responses.

    SUCCESS_SCHEMA_BY_OPERATION:
        Maps libfits operation names to schema identifiers for success
        responses.
"""

from __future__ import annotations

import json
from typing import Any

import jsonschema
from jsonschema import Draft202012Validator
from jsonschema.validators import validate

from pyfits import _native
from pyfits._errors import FitsError, FitsSchemaError
from pyfits.result import Err, Ok, Result

_SCHEMA_CACHE: dict[str, dict[str, Any]] = {}
_VALIDATOR_CACHE: dict[str, Draft202012Validator] = {}

# Schema ids embedded in libfits (``FITS_{id}_schema()``).
_LIBFITS_SCHEMA_IDS: tuple[str, ...] = (
    "validate_request",
    "validate_response",
    "output_graph_request",
    "new_node_request",
    "new_node_response",
    "new_link_request",
    "remove_request",
    "init_request",
    "register_node_type_request",
    "register_link_type_request",
    "error_response",
)

OK_TRUE_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["ok"],
    "properties": {"ok": {"const": True}},
}

OUTPUT_GRAPH_SUCCESS_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["ok", "graph"],
    "properties": {
        "ok": {"const": True},
        "graph": {"type": "object"},
    },
}

SUCCESS_SCHEMA_BY_OPERATION: dict[str, str] = {
    "validate": "validate_response",
    "new_node": "new_node_response",
    "output_graph": "output_graph_success",
    "init": "ok_true",
    "new_link": "ok_true",
    "remove": "ok_true",
    "register_node_type": "ok_true",
    "register_link_type": "ok_true",
}


def schema_ids() -> tuple[str, ...]:
    """Return known schema identifiers.

    Includes libfits embedded schema ids plus pyfits-local ``ok_true`` and
    ``output_graph_success``.

    Returns:
        Tuple of schema identifier strings.
    """
    return _LIBFITS_SCHEMA_IDS + ("ok_true", "output_graph_success")


def clear_schema_cache() -> None:
    """Clear cached libfits schemas and validators."""
    _SCHEMA_CACHE.clear()
    _VALIDATOR_CACHE.clear()


def schema_dict(schema_id: str) -> Result[dict[str, Any], FitsError]:
    """Return a parsed JSON Schema document.

    Args:
        schema_id: Schema identifier (libfits embedded id or pyfits-local
            ``ok_true`` / ``output_graph_success``).

    Returns:
        ``Ok(schema)`` on success, or ``Err(FitsError)`` when libfits schema
        loading fails.

    Raises:
        KeyError: Unknown schema id.
    """
    if schema_id == "ok_true":
        return Ok(OK_TRUE_SCHEMA)
    if schema_id == "output_graph_success":
        return Ok(OUTPUT_GRAPH_SUCCESS_SCHEMA)
    if schema_id not in _LIBFITS_SCHEMA_IDS:
        msg = f"unknown schema id: {schema_id}"
        raise KeyError(msg)
    cached = _SCHEMA_CACHE.get(schema_id)
    if cached is not None:
        return Ok(cached)
    fn_name = f"FITS_{schema_id}_schema"
    match _native.load_library():
        case Err(error):
            return Err(error)
        case Ok(loaded):
            raw = getattr(loaded, fn_name)()
            if raw is None:
                msg = f"{fn_name} returned NULL"
                return Err(FitsError(msg, code="schema_null"))
            parsed = json.loads(raw.decode("utf-8"))
            if not isinstance(parsed, dict):
                msg = f"{schema_id} schema is not a JSON object"
                return Err(
                    FitsSchemaError(
                        msg,
                        operation="schema",
                        schema_id=schema_id,
                    )
                )
            _SCHEMA_CACHE[schema_id] = parsed
            return Ok(parsed)


def validator(schema_id: str) -> Result[Draft202012Validator, FitsError]:
    """Return a compiled JSON Schema validator.

    Args:
        schema_id: Schema identifier passed to :func:`schema_dict`.

    Returns:
        ``Ok(validator)`` on success, or ``Err(FitsError)`` when schema loading
        fails.

    Raises:
        KeyError: Unknown schema id.
    """
    cached = _VALIDATOR_CACHE.get(schema_id)
    if cached is not None:
        return Ok(cached)
    match schema_dict(schema_id):
        case Ok(schema):
            compiled = Draft202012Validator(schema)
            _VALIDATOR_CACHE[schema_id] = compiled
            return Ok(compiled)
        case Err(error):
            return Err(error)


def validate_document(
    schema_id: str,
    doc: dict[str, Any],
) -> Result[None, FitsError | jsonschema.ValidationError]:
    """Validate a document against a schema.

    Args:
        schema_id: Schema identifier passed to :func:`schema_dict`.
        doc: JSON object to validate.

    Returns:
        ``Ok(None)`` when ``doc`` matches the schema, or ``Err`` with a
        validation or schema-load error.

    Raises:
        KeyError: Unknown schema id.
    """
    match schema_dict(schema_id):
        case Err(error):
            return Err(error)
        case Ok(schema):
            try:
                validate(instance=doc, schema=schema)
            except jsonschema.ValidationError as exc:
                return Err(exc)
            return Ok(None)
