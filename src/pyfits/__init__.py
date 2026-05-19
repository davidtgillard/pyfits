"""Python FITS file handling library."""

from importlib.metadata import PackageNotFoundError, version

from pyfits.core import example

try:
    __version__ = version("pyfits")
except PackageNotFoundError:
    # Package not installed (e.g. running from a bare checkout); see pyproject.toml.
    __version__ = "0.0.0+unknown"

__all__ = ["__version__", "example"]
