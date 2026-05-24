"""Unit tests for libfits C ABI helpers."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pyfits import _native
from pyfits._errors import FitsError
from pyfits._native import FitsApiVersion
from pyfits._version_abi import (
    api_version_minor,
    libfits_version_major,
    libfits_version_packed,
)
from pyfits.result import Err, Ok


def test_libfits_version_packed_success(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_lib = MagicMock()
    mock_lib.FITS_abi_version.return_value = FitsApiVersion(16, 1, 2, 0)
    monkeypatch.setattr(_native, "load_library", lambda: Ok(mock_lib))
    result = libfits_version_packed()
    assert isinstance(result, Ok)
    assert result.ok_value == 0x00010002


def test_libfits_version_major_success(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_lib = MagicMock()
    mock_lib.FITS_abi_version.return_value = FitsApiVersion(16, 3, 4, 0)
    monkeypatch.setattr(_native, "load_library", lambda: Ok(mock_lib))
    result = libfits_version_major()
    assert isinstance(result, Ok)
    assert result.ok_value == 3


def test_api_version_minor_success(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_lib = MagicMock()
    mock_lib.FITS_abi_version.return_value = FitsApiVersion(16, 3, 4, 0)
    monkeypatch.setattr(_native, "load_library", lambda: Ok(mock_lib))
    result = api_version_minor()
    assert isinstance(result, Ok)
    assert result.ok_value == 4


def test_version_helpers_propagate_load_error(monkeypatch: pytest.MonkeyPatch) -> None:
    err = FitsError("missing", code="lib_not_found")
    monkeypatch.setattr(_native, "load_library", lambda: Err(err))
    assert isinstance(libfits_version_packed(), Err)
    assert isinstance(libfits_version_major(), Err)
    assert isinstance(api_version_minor(), Err)
