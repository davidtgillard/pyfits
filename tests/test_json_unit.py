"""Unit tests for pyfits._json."""

from __future__ import annotations

import ctypes

import pytest

from pyfits._errors import FitsError
from pyfits._json import _c_operation, call_and_parse, dumps_request


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
        lambda *_args, **_kwargs: (status, text),
    )
    monkeypatch.setattr("pyfits._json._native.last_error", lambda: "native error")
    with pytest.raises(FitsError, match=match):
        call_and_parse("init", ctypes.c_void_p(1), {"no_interactive": True})


def test_call_and_parse_empty_response_fallback_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "pyfits._json._native.call_json",
        lambda *_args, **_kwargs: (-1, ""),
    )
    monkeypatch.setattr("pyfits._json._native.last_error", lambda: "")
    with pytest.raises(FitsError, match="status -1"):
        call_and_parse("init", ctypes.c_void_p(1), {"no_interactive": True})


def test_call_and_parse_bad_status_with_error_doc(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = '{"ok": false, "error": {"code": "E", "message": "fail"}}'
    monkeypatch.setattr(
        "pyfits._json._native.call_json",
        lambda *_args, **_kwargs: (-1, body),
    )
    monkeypatch.setattr("pyfits._json._native.last_error", lambda: "native error")
    with pytest.raises(FitsError, match="fail"):
        call_and_parse("init", ctypes.c_void_p(1), {"no_interactive": True})


def test_call_and_parse_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "pyfits._json._native.call_json",
        lambda *_args, **_kwargs: (0, '{"ok": true}'),
    )
    result = call_and_parse("init", ctypes.c_void_p(1), {"no_interactive": True})
    assert result == {"ok": True}
