"""Public access to libfits JSON Schemas."""

from __future__ import annotations

from jsonschema import Draft202012Validator

from pyfits._schemas import (
    OK_TRUE_SCHEMA,
    SUCCESS_SCHEMA_BY_OPERATION,
    schema_dict,
    schema_ids,
    validator,
)

__all__ = [
    "OK_TRUE_SCHEMA",
    "SUCCESS_SCHEMA_BY_OPERATION",
    "schema_dict",
    "schema_ids",
    "validator",
    "Draft202012Validator",
]
