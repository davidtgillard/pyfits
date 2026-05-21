"""Unit tests for schema loading error paths."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pyfits import _native
from pyfits._schemas import schema_dict, validator


@pytest.fixture(autouse=True)
def clear_schema_cache() -> None:
    schema_dict.cache_clear()
    validator.cache_clear()
    yield
    schema_dict.cache_clear()
    validator.cache_clear()


def test_schema_dict_unknown_id() -> None:
    with pytest.raises(KeyError, match="unknown schema id"):
        schema_dict("nope")


def test_schema_dict_null_from_c(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_lib = MagicMock()
    mock_lib.FITS_init_request_schema.return_value = None
    monkeypatch.setattr(_native, "_LIB", mock_lib)
    with pytest.raises(RuntimeError, match="returned NULL"):
        schema_dict("init_request")


def test_schema_dict_non_object_json(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_lib = MagicMock()
    mock_lib.FITS_init_request_schema.return_value = b'"string"'
    monkeypatch.setattr(_native, "_LIB", mock_lib)
    with pytest.raises(TypeError, match="not a JSON object"):
        schema_dict("init_request")
