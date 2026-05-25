"""Unit tests for pyfits.errors."""

from __future__ import annotations

from typing import Any

import pytest

from pyfits.errors import (
    FitsSchemaError,
    FitsStatus,
    _error_from_error_document,
    _error_from_status,
    _lib_not_found_error,
    _status_from_int,
)


@pytest.mark.parametrize(
    "value,expected",
    [
        (0, FitsStatus.OK),
        (-7, FitsStatus.ERR_ALREADY_INITIALIZED),
        (-12, FitsStatus.ERR_SUBGRAPH_INVALID),
        (-13, FitsStatus.ERR_UNKNOWN_NESTED_TYPE),
        (999, None),
    ],
)
def test_status_from_int(value: int, expected: FitsStatus | None) -> None:
    assert _status_from_int(value) == expected


@pytest.mark.parametrize(
    "doc",
    [
        {"ok": True},
    ],
)
def test_error_from_error_document_ok(doc: dict[str, Any]) -> None:
    assert _error_from_error_document(doc) is None


@pytest.mark.parametrize(
    "doc,match",
    [
        ({"ok": False, "error": "not-a-dict"}, "without an error object"),
        (
            {"ok": False, "error": {"code": 1, "message": "m"}},
            "missing code or message",
        ),
        (
            {"ok": False, "error": {"code": "E", "message": 1}},
            "missing code or message",
        ),
        (
            {"ok": False, "error": {"code": "E", "message": "msg"}},
            "msg",
        ),
    ],
)
def test_error_from_error_document_returns_error(
    doc: dict[str, Any],
    match: str,
) -> None:
    err = _error_from_error_document(doc)
    assert err is not None
    assert match in str(err)


def test_error_from_status_ok() -> None:
    assert _error_from_status(0, "") is None


@pytest.mark.parametrize(
    "status,last_error,match",
    [
        (-1, "detail", "detail"),
        (-1, "", "status -1"),
    ],
)
def test_error_from_status_returns_error(
    status: int,
    last_error: str,
    match: str,
) -> None:
    err = _error_from_status(status, last_error)
    assert err is not None
    assert match in str(err)
    assert err.status == FitsStatus.ERR_INVALID_ARGUMENT


def test_lib_not_found_error() -> None:
    err = _lib_not_found_error("missing")
    assert err.code == "lib_not_found"
    assert str(err) == "missing"


def test_fits_schema_error_attributes() -> None:
    err = FitsSchemaError(
        "bad",
        operation="validate",
        schema_id="invariant",
        validation_message="field required",
    )
    assert err.operation == "validate"
    assert err.schema_id == "invariant"
    assert err.validation_message == "field required"
