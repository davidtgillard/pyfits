"""Unit tests for schema loading error paths."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pyfits import _native
from pyfits._errors import FitsError, FitsSchemaError
from pyfits._schemas import clear_schema_cache, schema_dict, validator
from pyfits.result import Err, Ok


@pytest.fixture(autouse=True)
def clear_schema_cache_fixture() -> None:
    clear_schema_cache()
    yield
    clear_schema_cache()


def test_schema_dict_unknown_id() -> None:
    with pytest.raises(KeyError, match="unknown schema id"):
        schema_dict("nope")


def test_schema_dict_null_from_c(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_lib = MagicMock()
    mock_lib.FITS_init_request_schema.return_value = None
    monkeypatch.setattr(_native, "_LIB", mock_lib)
    monkeypatch.setattr(_native, "load_library", lambda: Ok(mock_lib))
    result = schema_dict("init_request")
    assert isinstance(result, Err)
    assert isinstance(result.err_value, FitsError)
    assert "returned NULL" in str(result.err_value)


def test_schema_dict_non_object_json(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_lib = MagicMock()
    mock_lib.FITS_init_request_schema.return_value = b'"string"'
    monkeypatch.setattr(_native, "_LIB", mock_lib)
    monkeypatch.setattr(_native, "load_library", lambda: Ok(mock_lib))
    result = schema_dict("init_request")
    assert isinstance(result, Err)
    assert isinstance(result.err_value, FitsSchemaError)
    assert "not a JSON object" in str(result.err_value)


def test_schema_dict_local_ok_true() -> None:
    result = schema_dict("ok_true")
    assert isinstance(result, Ok)
    assert result.ok_value["properties"]["ok"]["const"] is True


def test_validator_returns_err_when_schema_load_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        _native,
        "load_library",
        lambda: Err(FitsError("missing", code="lib_not_found")),
    )
    result = validator("init_request")
    assert isinstance(result, Err)
