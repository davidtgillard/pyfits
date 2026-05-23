"""libfits C ABI and package version (read from the loaded shared library)."""


def libfits_version_packed() -> int:
    """Return the packed libfits C ABI version.

    Reads ``FITS_api_version()`` from the loaded shared library.

    Returns:
        Packed version integer: ``(major << 16) | minor``.

    Raises:
        OSError: When the libfits shared library cannot be found or loaded.
    """
    from pyfits._native import lib

    return int(lib().FITS_api_version())


def libfits_version_major() -> int:
    """Return the major component of the loaded libfits C struct ABI.

    Returns:
        Major version extracted from :func:`libfits_version_packed`.

    Raises:
        OSError: When the libfits shared library cannot be found or loaded.
    """
    return libfits_version_packed() >> 16


def api_version_minor() -> int:
    """Return the minor component of the loaded libfits C struct ABI.

    Returns:
        Minor version extracted from :func:`libfits_version_packed`.

    Raises:
        OSError: When the libfits shared library cannot be found or loaded.
    """
    return libfits_version_packed() & 0xFFFF
