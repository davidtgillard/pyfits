"""Unit tests for libfits C ABI helpers."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pyfits import _version_abi
from pyfits._native import FitsApiVersion
from pyfits._version_abi import Version, get_version


def test_version_cannot_be_constructed_directly() -> None:
    with pytest.raises(TypeError, match="use get_version"):
        Version(major=3, minor=4, patch=5)


def test_version_string_from_components(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_lib = MagicMock()
    mock_lib.FITS_abi_version.return_value = FitsApiVersion(16, 3, 4, 5)
    monkeypatch.setattr(_version_abi, "lib", lambda: mock_lib)
    version = _version_abi._read_version()
    assert version.version_string == "3.4.5"


def test_get_version_returns_import_time_snapshot() -> None:
    first = get_version()
    second = get_version()
    assert first is second
