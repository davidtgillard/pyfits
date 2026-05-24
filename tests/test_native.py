"""Smoke tests for libfits loading."""

from __future__ import annotations

from support import unwrap

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
    ver = native.lib().FITS_abi_version()
    packed = (ver.major << 16) | ver.minor
    assert unwrap(libfits_version_packed()) == packed
    assert unwrap(libfits_version_major()) == ver.major
    assert unwrap(api_version_minor()) == ver.minor


def test_version_string() -> None:
    assert unwrap(libfits_version_string())
    assert unwrap(lib_path()).is_file()
