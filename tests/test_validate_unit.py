"""Response validation without libfits calls."""

from __future__ import annotations

import pytest

from pyfits._validate import validate_response
from pyfits.errors import FitsSchemaError
from pyfits.result import Err, Ok


def test_ok_true_valid() -> None:
    result = validate_response("init", {"ok": True})
    assert isinstance(result, Ok)


def test_ok_true_rejects_false() -> None:
    from pyfits._schemas import SchemaId, validate_document

    result = validate_document(SchemaId.OK_TRUE, {"ok": False})
    assert isinstance(result, Err)


def test_error_path_uses_error_schema() -> None:
    result = validate_response(
        "init",
        {"ok": False, "error": {"code": "e", "message": "m"}},
    )
    assert isinstance(result, Ok)


def test_error_response_valid() -> None:
    result = validate_response(
        "init",
        {"ok": False, "error": {"code": "AlreadyInitialized", "message": "already"}},
    )
    assert isinstance(result, Ok)


def test_validate_success_minimal_fails_invariants_later() -> None:
    # Schema allows ok-only; models layer enforces validation_issues.
    result = validate_response(
        "validate",
        {
            "ok": True,
            "protocol_version": 2,
            "validation_issues": [],
            "summary": {
                "total_validation_issues": 0,
                "info_count": 0,
                "warning_count": 0,
                "error_count": 0,
            },
        },
    )
    assert isinstance(result, Ok)


def test_unknown_operation_raises_key_error() -> None:
    with pytest.raises(KeyError, match="unknown operation"):
        validate_response("not_an_op", {"ok": True})


def test_schema_validation_wrapped_as_fits_schema_error() -> None:
    result = validate_response("init", {"ok": True, "extra": "bad"})
    assert isinstance(result, Err)
    assert isinstance(result.err_value, FitsSchemaError)
    assert "failed schema" in str(result.err_value)
