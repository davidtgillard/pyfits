"""Unit tests for pyfits re-exports of the result library."""

from __future__ import annotations

import pytest
from result import UnwrapError

from pyfits.result import Err, Ok


def test_reexports_is_ok_is_err() -> None:
    from pyfits.result import is_err, is_ok

    assert is_ok(Ok(1))
    assert is_err(Err("x"))


def test_ok_is_ok() -> None:
    result = Ok("yay")
    assert result.is_ok()
    assert not result.is_err()
    assert result.unwrap() == "yay"
    assert result.ok_value == "yay"


def test_err_is_err() -> None:
    result = Err("bad")
    assert result.is_err()
    assert not result.is_ok()
    with pytest.raises(UnwrapError):
        result.unwrap()
    assert result.err_value == "bad"


def test_ok_map() -> None:
    result = Ok(2).map(lambda value: value * 3)
    assert isinstance(result, Ok)
    assert result.ok_value == 6


def test_err_map() -> None:
    result = Err("bad").map(lambda value: value * 3)
    assert isinstance(result, Err)
    assert result.err_value == "bad"
