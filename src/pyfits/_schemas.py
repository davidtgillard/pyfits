"""Load and cache JSON Schemas embedded in libfits.

Constants:

    SchemaId:
        Fixed enum of schema identifiers accepted by :func:`schema_dict`.

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
from enum import StrEnum
from typing import Any

import jsonschema
from jsonschema import Draft202012Validator
from jsonschema.validators import validate

from pyfits import _native
from pyfits.errors import FitsError, FitsSchemaError
from pyfits.result import Err, Ok, Result

_SCHEMA_CACHE: dict[SchemaId, dict[str, Any]] = {}
_VALIDATOR_CACHE: dict[SchemaId, Draft202012Validator] = {}


class SchemaId(StrEnum):
    """Known JSON Schema identifiers for libfits and pyfits-local schemas.

    Members include libfits embedded request/response ids (for example
    ``VALIDATE_REQUEST``, ``ERROR_RESPONSE``) and pyfits-local success ids
    ``OK_TRUE`` and ``OUTPUT_GRAPH_SUCCESS``. Use :func:`schema_ids` for the
    full list.
    """

    VALIDATE_REQUEST = "validate_request"
    VALIDATE_RESPONSE = "validate_response"
    OUTPUT_GRAPH_REQUEST = "output_graph_request"
    NEW_NODE_REQUEST = "new_node_request"
    NEW_NODE_RESPONSE = "new_node_response"
    NEW_LINK_REQUEST = "new_link_request"
    NEW_LINK_RESPONSE = "new_link_response"
    REMOVE_REQUEST = "remove_request"
    INIT_REQUEST = "init_request"
    REGISTER_NODE_TYPE_REQUEST = "register_node_type_request"
    REGISTER_LINK_TYPE_REQUEST = "register_link_type_request"
    RENAME_INSTANCE_REQUEST = "rename_instance_request"
    RENAME_INSTANCE_RESPONSE = "rename_instance_response"
    REGISTER_NESTED_NODE_TYPE_REQUEST = "register_nested_node_type_request"
    REGISTER_NESTED_LINK_TYPE_REQUEST = "register_nested_link_type_request"
    ERROR_RESPONSE = "error_response"
    OK_TRUE = "ok_true"
    OUTPUT_GRAPH_SUCCESS = "output_graph_success"


# Schema ids embedded in libfits (``FITS_{id}_schema()``).
_LIBFITS_SCHEMA_IDS: frozenset[SchemaId] = frozenset(
    schema_id
    for schema_id in SchemaId
    if schema_id not in (SchemaId.OK_TRUE, SchemaId.OUTPUT_GRAPH_SUCCESS)
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

SUCCESS_SCHEMA_BY_OPERATION: dict[str, SchemaId] = {
    "validate": SchemaId.VALIDATE_RESPONSE,
    "new_node": SchemaId.NEW_NODE_RESPONSE,
    "output_graph": SchemaId.OUTPUT_GRAPH_SUCCESS,
    "init": SchemaId.OK_TRUE,
    "new_link": SchemaId.NEW_LINK_RESPONSE,
    "remove": SchemaId.OK_TRUE,
    "rename_instance": SchemaId.RENAME_INSTANCE_RESPONSE,
    "register_node_type": SchemaId.OK_TRUE,
    "register_link_type": SchemaId.OK_TRUE,
    "register_nested_node_type": SchemaId.OK_TRUE,
    "register_nested_link_type": SchemaId.OK_TRUE,
}


def schema_ids() -> tuple[SchemaId, ...]:
    """Return known schema identifiers.

    Includes libfits embedded schema ids plus pyfits-local ``ok_true`` and
    ``output_graph_success``.

    Returns:
        Tuple of :class:`SchemaId` values.
    """
    return tuple(SchemaId)


def clear_schema_cache() -> None:
    """Clear cached libfits schemas and validators."""
    _SCHEMA_CACHE.clear()
    _VALIDATOR_CACHE.clear()


def schema_dict(schema_id: SchemaId) -> Result[dict[str, Any], FitsError]:
    """Return a parsed JSON Schema document.

    Args:
        schema_id: Schema identifier (libfits embedded id or pyfits-local
            ``SchemaId.OK_TRUE`` / ``SchemaId.OUTPUT_GRAPH_SUCCESS``).

    Returns:
        ``Ok(schema)`` on success, or ``Err(FitsError)`` when libfits schema
        loading fails.
    """
    if schema_id is SchemaId.OK_TRUE:
        return Ok(OK_TRUE_SCHEMA)
    if schema_id is SchemaId.OUTPUT_GRAPH_SUCCESS:
        return Ok(OUTPUT_GRAPH_SUCCESS_SCHEMA)
    if schema_id not in _LIBFITS_SCHEMA_IDS:
        msg = f"schema id is not embedded in libfits: {schema_id}"
        raise ValueError(msg)
    cached = _SCHEMA_CACHE.get(schema_id)
    if cached is not None:
        return Ok(cached)
    fn_name = f"FITS_{schema_id.value}_schema"
    loaded = _native._LIB
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


def validator(schema_id: SchemaId) -> Result[Draft202012Validator, FitsError]:
    """Return a compiled JSON Schema validator.

    Args:
        schema_id: Schema identifier passed to :func:`schema_dict`.

    Returns:
        ``Ok(validator)`` on success, or ``Err(FitsError)`` when schema loading
        fails.
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
    schema_id: SchemaId,
    doc: dict[str, Any],
) -> Result[None, FitsError | jsonschema.ValidationError]:
    """Validate a document against a schema.

    Args:
        schema_id: Schema identifier passed to :func:`schema_dict`.
        doc: JSON object to validate.

    Returns:
        ``Ok(None)`` when ``doc`` matches the schema, or ``Err`` with a
        validation or schema-load error.
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
