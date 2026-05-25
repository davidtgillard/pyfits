"""Unit tests for schema loading error paths."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pyfits import _native
from pyfits._schemas import (
    SchemaId,
    clear_schema_cache,
    schema_dict,
    validate_document,
)
from pyfits.errors import FitsError, FitsSchemaError
from pyfits.result import Err, Ok


@pytest.fixture(autouse=True)
def clear_schema_cache_fixture() -> None:
    clear_schema_cache()
    yield
    clear_schema_cache()


def test_schema_dict_unknown_id() -> None:
    with pytest.raises(ValueError, match="is not a valid SchemaId"):
        SchemaId("nope")


def test_schema_dict_null_from_c(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_lib = MagicMock()
    mock_lib.FITS_init_request_schema.return_value = None
    monkeypatch.setattr(_native, "_LIB", mock_lib)
    monkeypatch.setattr(_native, "load_library", lambda: Ok(mock_lib))
    result = schema_dict(SchemaId.INIT_REQUEST)
    assert isinstance(result, Err)
    assert isinstance(result.err_value, FitsError)
    assert "returned NULL" in str(result.err_value)


def test_schema_dict_non_object_json(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_lib = MagicMock()
    mock_lib.FITS_init_request_schema.return_value = b'"string"'
    monkeypatch.setattr(_native, "_LIB", mock_lib)
    monkeypatch.setattr(_native, "load_library", lambda: Ok(mock_lib))
    result = schema_dict(SchemaId.INIT_REQUEST)
    assert isinstance(result, Err)
    assert isinstance(result.err_value, FitsSchemaError)
    assert "not a JSON object" in str(result.err_value)


def test_schema_dict_local_ok_true() -> None:
    result = schema_dict(SchemaId.OK_TRUE)
    assert isinstance(result, Ok)
    assert result.ok_value["properties"]["ok"]["const"] is True


def test_validate_document_success_for_local_schemas() -> None:
    assert isinstance(validate_document(SchemaId.OK_TRUE, {"ok": True}), Ok)
    assert isinstance(
        validate_document(
            SchemaId.OUTPUT_GRAPH_SUCCESS,
            {"ok": True, "graph": {"nodes": [], "edges": []}},
        ),
        Ok,
    )


def test_validate_document_invalid_instance() -> None:
    result = validate_document(SchemaId.OK_TRUE, {"ok": False})
    assert isinstance(result, Err)


def test_schema_dict_uses_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_schema_cache()
    mock_lib = MagicMock()
    mock_lib.FITS_init_request_schema.return_value = b'{"type":"object"}'
    monkeypatch.setattr(_native, "_LIB", mock_lib)
    monkeypatch.setattr(_native, "load_library", lambda: Ok(mock_lib))
    first = schema_dict(SchemaId.INIT_REQUEST)
    second = schema_dict(SchemaId.INIT_REQUEST)
    assert isinstance(first, Ok)
    assert isinstance(second, Ok)
    mock_lib.FITS_init_request_schema.assert_called_once()


def test_validator_uses_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_schema_cache()
    mock_lib = MagicMock()
    mock_lib.FITS_init_request_schema.return_value = b'{"type":"object"}'
    monkeypatch.setattr(_native, "_LIB", mock_lib)
    monkeypatch.setattr(_native, "load_library", lambda: Ok(mock_lib))
    from pyfits._schemas import validator

    first = validator(SchemaId.INIT_REQUEST)
    second = validator(SchemaId.INIT_REQUEST)
    assert isinstance(first, Ok)
    assert isinstance(second, Ok)
    mock_lib.FITS_init_request_schema.assert_called_once()


def test_validator_schema_load_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_schema_cache()
    mock_lib = MagicMock()
    mock_lib.FITS_init_request_schema.return_value = None
    monkeypatch.setattr(_native, "_LIB", mock_lib)
    monkeypatch.setattr(_native, "load_library", lambda: Ok(mock_lib))
    from pyfits._schemas import validator

    result = validator(SchemaId.INIT_REQUEST)
    assert isinstance(result, Err)


def test_validate_document_schema_load_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_schema_cache()
    mock_lib = MagicMock()
    mock_lib.FITS_init_request_schema.return_value = None
    monkeypatch.setattr(_native, "_LIB", mock_lib)
    monkeypatch.setattr(_native, "load_library", lambda: Ok(mock_lib))
    result = validate_document(SchemaId.INIT_REQUEST, {"protocol_version": 1})
    assert isinstance(result, Err)
