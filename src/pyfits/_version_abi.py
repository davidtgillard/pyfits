"""libfits C ABI and package version (read from the loaded shared library)."""


def libfits_version_packed() -> int:
    """Return ``FITS_api_version()``: ``(major << 16) | minor``."""
    from pyfits._native import lib

    return int(lib().FITS_api_version())


def libfits_version_major() -> int:
    """Return the major component of the loaded libfits C struct ABI."""
    return libfits_version_packed() >> 16


def api_version_minor() -> int:
    """Return the minor component of the loaded libfits C struct ABI."""
    return libfits_version_packed() & 0xFFFF
