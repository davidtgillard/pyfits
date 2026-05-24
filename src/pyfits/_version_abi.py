"""libfits C ABI and package version (read from the loaded shared library)."""

from pyfits._errors import FitsError
from pyfits.result import Err, Ok, Result


def libfits_version_packed() -> Result[int, FitsError]:
    """Return the packed libfits C ABI version.

    Reads ``FITS_abi_version()`` from the loaded shared library.

    Returns:
        ``Ok(packed)`` where packed is ``(major << 16) | minor``, or
        ``Err(FitsError)`` when the library cannot be loaded.
    """
    from pyfits._native import load_library

    match load_library():
        case Ok(loaded):
            ver = loaded.FITS_abi_version()
            return Ok((int(ver.major) << 16) | int(ver.minor))
        case Err(error):
            return Err(error)


def libfits_version_major() -> Result[int, FitsError]:
    """Return the major component of the loaded libfits C struct ABI.

    Returns:
        ``Ok(major)`` extracted from :func:`libfits_version_packed`, or
        ``Err(FitsError)`` when the library cannot be loaded.
    """
    match libfits_version_packed():
        case Ok(packed):
            return Ok(packed >> 16)
        case Err(error):
            return Err(error)


def api_version_minor() -> Result[int, FitsError]:
    """Return the minor component of the loaded libfits C struct ABI.

    Returns:
        ``Ok(minor)`` extracted from :func:`libfits_version_packed`, or
        ``Err(FitsError)`` when the library cannot be loaded.
    """
    match libfits_version_packed():
        case Ok(packed):
            return Ok(packed & 0xFFFF)
        case Err(error):
            return Err(error)
