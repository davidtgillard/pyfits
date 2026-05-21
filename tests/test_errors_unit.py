"""Unit tests for pyfits._errors."""

from __future__ import annotations

from typing import Any

import pytest

from pyfits._errors import (
    FitsError,
    FitsSchemaError,
    FitsStatus,
    raise_for_error_document,
    raise_for_status,
    status_from_int,
)


@pytest.mark.parametrize(
    "value,expected",
    [
        (0, FitsStatus.OK),
        (-7, FitsStatus.ERR_ALREADY_INITIALIZED),
        (999, None),
    ],
)
def test_status_from_int(value: int, expected: FitsStatus | None) -> None:
    assert status_from_int(value) == expected


@pytest.mark.parametrize(
    "doc",
    [
        {"ok": True},
    ],
)
def test_raise_for_error_document_ok(doc: dict[str, Any]) -> None:
    raise_for_error_document(doc)


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
def test_raise_for_error_document_raises(doc: dict[str, Any], match: str) -> None:
    with pytest.raises(FitsError, match=match):
        raise_for_error_document(doc)


def test_raise_for_status_ok() -> None:
    raise_for_status(0, "")


@pytest.mark.parametrize(
    "status,last_error,match",
    [
        (-1, "detail", "detail"),
        (-1, "", "status -1"),
    ],
)
def test_raise_for_status_raises(status: int, last_error: str, match: str) -> None:
    with pytest.raises(FitsError, match=match) as exc_info:
        raise_for_status(status, last_error)
    assert exc_info.value.status == FitsStatus.ERR_INVALID_ARGUMENT


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
