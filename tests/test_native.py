"""Smoke tests for libfits loading."""

from __future__ import annotations

from pyfits import _native as native
from pyfits import get_version


def test_lib_loads() -> None:
    lib = native.lib()
    assert lib is not None


def test_api_version() -> None:
    ver = native.lib().FITS_abi_version()
    version = get_version()
    assert version.major == ver.major
    assert version.minor == ver.minor
    assert version.patch == ver.patch
    assert version.version_string == f"{ver.major}.{ver.minor}.{ver.patch}"


def test_version_string() -> None:
    version = get_version()
    assert version.version_string
