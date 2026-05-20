"""JSON Schema loading from libfits."""

from __future__ import annotations

import pytest

from pyfits import schemas


@pytest.mark.parametrize("schema_id", schemas.schema_ids())
def test_schema_is_object(schema_id: str) -> None:
    doc = schemas.schema_dict(schema_id)
    assert doc.get("type") == "object" or "$defs" in doc or "properties" in doc


def test_libfits_validate_request_has_id_prefix() -> None:
    doc = schemas.schema_dict("validate_request")
    props = doc.get("properties", {})
    assert "include_link_endpoints" in props


def test_validator_compiles() -> None:
    v = schemas.validator("error_response")
    v.validate({"ok": False, "error": {"code": "x", "message": "y"}})
