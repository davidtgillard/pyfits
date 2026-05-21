"""Load and cache JSON Schemas embedded in libfits."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.validators import validate

from pyfits import _native

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

# pyfits-local minimal success schema when libfits has no response schema.
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
    """Return known schema identifiers (includes pyfits-local ``ok_true``)."""
    return _LIBFITS_SCHEMA_IDS + ("ok_true", "output_graph_success")


@lru_cache(maxsize=32)
def schema_dict(schema_id: str) -> dict[str, Any]:
    """Return a parsed JSON Schema document.

    Args:
        schema_id: Schema identifier (libfits embedded id or pyfits-local
            ``ok_true`` / ``output_graph_success``).

    Returns:
        Parsed JSON Schema object.

    Raises:
        KeyError: Unknown schema id.
        RuntimeError: libfits schema accessor returned NULL.
        TypeError: Parsed schema is not a JSON object.
    """
    if schema_id == "ok_true":
        return OK_TRUE_SCHEMA
    if schema_id == "output_graph_success":
        return OUTPUT_GRAPH_SUCCESS_SCHEMA
    if schema_id not in _LIBFITS_SCHEMA_IDS:
        msg = f"unknown schema id: {schema_id}"
        raise KeyError(msg)
    fn_name = f"FITS_{schema_id}_schema"
    raw = getattr(_native.lib(), fn_name)()
    if raw is None:
        msg = f"{fn_name} returned NULL"
        raise RuntimeError(msg)
    parsed = json.loads(raw.decode("utf-8"))
    if not isinstance(parsed, dict):
        msg = f"{schema_id} schema is not a JSON object"
        raise TypeError(msg)
    return parsed


@lru_cache(maxsize=32)
def validator(schema_id: str) -> Draft202012Validator:
    """Return a compiled JSON Schema validator.

    Args:
        schema_id: Schema identifier passed to :func:`schema_dict`.

    Returns:
        Compiled Draft 2020-12 validator for the schema.
    """
    return Draft202012Validator(schema_dict(schema_id))


def validate_document(schema_id: str, doc: dict[str, Any]) -> None:
    """Validate doc against schema_id; raises jsonschema.ValidationError on failure."""
    validate(instance=doc, schema=schema_dict(schema_id))
