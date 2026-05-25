"""Unit tests for pyfits._json."""

from __future__ import annotations

import ctypes

import pytest

from pyfits._json import _c_operation, call_and_parse, dumps_request
from pyfits.errors import FitsError
from pyfits.result import Err, Ok


@pytest.mark.parametrize(
    "operation,expected",
    [
        ("remove", "remove_obj"),
        ("init", "init"),
    ],
)
def test_c_operation(operation: str, expected: str) -> None:
    assert _c_operation(operation) == expected


def test_dumps_request_none() -> None:
    assert dumps_request(None) is None


def test_dumps_request_encodes_json() -> None:
    assert dumps_request({"a": 1}) == b'{"a":1}'


@pytest.mark.parametrize(
    "status,text,match",
    [
        (-1, "", "native error"),
        (0, "not-json", "invalid JSON"),
        (0, "[1]", "must be a JSON object"),
    ],
)
def test_call_and_parse_failures(
    monkeypatch: pytest.MonkeyPatch,
    status: int,
    text: str,
    match: str,
) -> None:
    monkeypatch.setattr(
        "pyfits._json._native.call_json",
        lambda *_args, **_kwargs: Ok((status, text)),
    )
    monkeypatch.setattr(
        "pyfits._json._native.last_error",
        lambda: Ok("native error"),
    )
    result = call_and_parse("init", ctypes.c_void_p(1), {})
    assert isinstance(result, Err)
    assert match in str(result.err_value)


def test_call_and_parse_empty_response_fallback_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "pyfits._json._native.call_json",
        lambda *_args, **_kwargs: Ok((-1, "")),
    )
    monkeypatch.setattr(
        "pyfits._json._native.last_error",
        lambda: Ok(""),
    )
    result = call_and_parse("init", ctypes.c_void_p(1), {})
    assert isinstance(result, Err)
    assert "status -1" in str(result.err_value)


def test_call_and_parse_bad_status_with_error_doc(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = '{"ok": false, "error": {"code": "E", "message": "fail"}}'
    monkeypatch.setattr(
        "pyfits._json._native.call_json",
        lambda *_args, **_kwargs: Ok((-1, body)),
    )
    monkeypatch.setattr(
        "pyfits._json._native.last_error",
        lambda: Ok("native error"),
    )
    result = call_and_parse("init", ctypes.c_void_p(1), {})
    assert isinstance(result, Err)
    assert "fail" in str(result.err_value)


def test_call_and_parse_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "pyfits._json._native.call_json",
        lambda *_args, **_kwargs: Ok((0, '{"ok": true}')),
    )
    result = call_and_parse("init", ctypes.c_void_p(1), {})
    assert isinstance(result, Ok)
    assert result.ok_value == {"ok": True}


def test_call_and_parse_empty_success_body(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "pyfits._json._native.call_json",
        lambda *_args, **_kwargs: Ok((0, "")),
    )
    result = call_and_parse("init", ctypes.c_void_p(1), {})
    assert isinstance(result, Ok)
    assert result.ok_value == {}


def test_call_and_parse_ok_false_at_success_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = '{"ok": false, "error": {"code": "E", "message": "nope"}}'
    monkeypatch.setattr(
        "pyfits._json._native.call_json",
        lambda *_args, **_kwargs: Ok((0, body)),
    )
    result = call_and_parse("init", ctypes.c_void_p(1), {})
    assert isinstance(result, Err)
    assert "nope" in str(result.err_value)
    monkeypatch.setattr(
        "pyfits._json._native.call_json",
        lambda *_args, **_kwargs: Err(FitsError("boom")),
    )
    result = call_and_parse("init", ctypes.c_void_p(1), {})
    assert isinstance(result, Err)
    assert str(result.err_value) == "boom"


def test_call_and_parse_last_error_load_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "pyfits._json._native.call_json",
        lambda *_args, **_kwargs: Ok((-1, "")),
    )
    monkeypatch.setattr(
        "pyfits._json._native.last_error",
        lambda: Err(FitsError("load failed")),
    )
    result = call_and_parse("init", ctypes.c_void_p(1), {})
    assert isinstance(result, Err)
    assert str(result.err_value) == "load failed"


def test_call_and_parse_validate_response_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from pyfits.errors import FitsSchemaError

    monkeypatch.setattr(
        "pyfits._json._native.call_json",
        lambda *_args, **_kwargs: Ok((0, '{"ok": true, "extra": "bad"}')),
    )
    result = call_and_parse("init", ctypes.c_void_p(1), {})
    assert isinstance(result, Err)
    assert isinstance(result.err_value, FitsSchemaError)


def test_call_and_parse_negative_status_after_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "pyfits._json._native.call_json",
        lambda *_args, **_kwargs: Ok((-1, '{"ok": true}')),
    )
    monkeypatch.setattr(
        "pyfits._json._native.last_error",
        lambda: Ok("status failure"),
    )
    result = call_and_parse("init", ctypes.c_void_p(1), {})
    assert isinstance(result, Err)
    assert "status failure" in str(result.err_value)


def test_call_and_parse_negative_status_last_error_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "pyfits._json._native.call_json",
        lambda *_args, **_kwargs: Ok((-1, '{"ok": true}')),
    )
    monkeypatch.setattr(
        "pyfits._json._native.last_error",
        lambda: Err(FitsError("diag failed")),
    )
    result = call_and_parse("init", ctypes.c_void_p(1), {})
    assert isinstance(result, Err)
    assert str(result.err_value) == "diag failed"


def test_call_and_parse_call_json_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "pyfits._json._native.call_json",
        lambda *_args, **_kwargs: Err(FitsError("call failed")),
    )
    result = call_and_parse("init", ctypes.c_void_p(1), {})
    assert isinstance(result, Err)
    assert str(result.err_value) == "call failed"


def test_call_and_parse_empty_body_status_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "pyfits._json._native.call_json",
        lambda *_args, **_kwargs: Ok((0, "")),
    )
    monkeypatch.setattr(
        "pyfits._json._native.last_error",
        lambda: Ok(""),
    )
    result = call_and_parse("init", ctypes.c_void_p(1), {})
    assert isinstance(result, Ok)
    assert result.ok_value == {}
