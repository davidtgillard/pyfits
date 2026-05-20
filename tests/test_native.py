"""Smoke tests for libfits loading."""

from __future__ import annotations

from pyfits import _native as native
from pyfits import (
    api_version_minor,
    lib_path,
    libfits_version_major,
    libfits_version_packed,
    libfits_version_string,
)


def test_lib_loads() -> None:
    lib = native.lib()
    assert lib is not None


def test_api_version() -> None:
    packed = int(native.lib().FITS_api_version())
    assert libfits_version_packed() == packed
    assert libfits_version_major() == (packed >> 16)
    assert api_version_minor() == (packed & 0xFFFF)


def test_version_string() -> None:
    assert libfits_version_string()
    assert lib_path().is_file()
