"""JSON Schema loading from libfits."""

from __future__ import annotations

import pytest
from support import unwrap

from pyfits import schemas


@pytest.mark.parametrize("schema_id", schemas.schema_ids())
def test_schema_is_object(schema_id: schemas.SchemaId) -> None:
    doc = unwrap(schemas.schema_dict(schema_id))
    assert doc.get("type") == "object" or "$defs" in doc or "properties" in doc


def test_libfits_validate_request_fields() -> None:
    doc = unwrap(schemas.schema_dict(schemas.SchemaId.VALIDATE_REQUEST))
    props = doc.get("properties", {})
    assert "include_link_endpoints" in props
    assert "include_nested_subgraphs" in props


def test_libfits_new_node_request_uses_type_name() -> None:
    doc = unwrap(schemas.schema_dict(schemas.SchemaId.NEW_NODE_REQUEST))
    assert "type_name" in doc.get("required", [])
    assert "id_prefix" not in doc.get("properties", {})


def test_libfits_output_graph_request_has_include_nested() -> None:
    doc = unwrap(schemas.schema_dict(schemas.SchemaId.OUTPUT_GRAPH_REQUEST))
    assert "include_nested" in doc.get("properties", {})


def test_new_schemas_load_from_libfits() -> None:
    for schema_id in (
        schemas.SchemaId.NEW_LINK_RESPONSE,
        schemas.SchemaId.RENAME_INSTANCE_REQUEST,
        schemas.SchemaId.RENAME_INSTANCE_RESPONSE,
    ):
        doc = unwrap(schemas.schema_dict(schema_id))
        assert doc.get("type") == "object"


def test_validator_compiles() -> None:
    v = unwrap(schemas.validator(schemas.SchemaId.ERROR_RESPONSE))
    v.validate({"ok": False, "error": {"code": "x", "message": "y"}})
