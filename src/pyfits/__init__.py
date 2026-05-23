"""Python bindings for libfits (fits graph repository engine).

Public exports:

    Repo:
        Session API for opening and mutating a fits repository.

    ObjectTypeName:
        Validated object type name for ``new_node``.

    ValidateResult, ValidateSummary, ValidationIssue:
        Typed models for ``validate`` responses.

    FitsError, FitsSchemaError, FitsStatus:
        Error types and stable libfits status codes.

    lib_path, libfits_version_string:
        Shared library location and version string.

    libfits_version_major, api_version_minor, libfits_version_packed:
        Loaded libfits C ABI version components.

    __version__:
        Installed pyfits package version from distribution metadata.
"""

from importlib.metadata import PackageNotFoundError, version

from pyfits._errors import FitsError, FitsSchemaError, FitsStatus
from pyfits._native import lib_path
from pyfits._native import version_string as libfits_version_string
from pyfits._version_abi import (
    api_version_minor,
    libfits_version_major,
    libfits_version_packed,
)
from pyfits.models import (
    ObjectTypeName,
    ValidateResult,
    ValidateSummary,
    ValidationIssue,
)
from pyfits.repo import Repo

try:
    __version__ = version("pyfits")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"

__all__ = [
    "FitsError",
    "FitsSchemaError",
    "FitsStatus",
    "ObjectTypeName",
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
