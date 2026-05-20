"""Python bindings for libfits (fits graph repository engine)."""

from importlib.metadata import PackageNotFoundError, version

from pyfits._errors import FitsError, FitsSchemaError, FitsStatus
from pyfits._native import lib_path
from pyfits._native import version_string as libfits_version_string
from pyfits._version_abi import (
    api_version_minor,
    libfits_version_major,
    libfits_version_packed,
)
from pyfits.models import ValidateResult, ValidateSummary, ValidationIssue
from pyfits.repo import Repo

try:
    __version__ = version("pyfits")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"

__all__ = [
    "FitsError",
    "FitsSchemaError",
    "FitsStatus",
    "Repo",
    "ValidateResult",
    "ValidateSummary",
    "ValidationIssue",
    "__version__",
    "libfits_version_major",
    "api_version_minor",
    "libfits_version_packed",
    "libfits_version_string",
    "lib_path",
]
