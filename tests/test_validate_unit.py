"""Response validation without libfits calls."""

from __future__ import annotations

import pytest

from pyfits._validate import validate_response


def test_ok_true_valid() -> None:
    validate_response("init", {"ok": True})


def test_ok_true_rejects_false() -> None:
    import jsonschema

    from pyfits._schemas import validate_document

    with pytest.raises(jsonschema.ValidationError):
        validate_document("ok_true", {"ok": False})


def test_error_path_uses_error_schema() -> None:
    validate_response(
        "init",
        {"ok": False, "error": {"code": "e", "message": "m"}},
    )


def test_error_response_valid() -> None:
    validate_response(
        "init",
        {"ok": False, "error": {"code": "AlreadyInitialized", "message": "already"}},
    )


def test_validate_success_minimal_fails_invariants_later() -> None:
    # Schema allows ok-only; models layer enforces validation_issues.
    validate_response(
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
