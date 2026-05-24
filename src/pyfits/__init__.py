"""Python bindings for libfits (fits graph repository engine).

Public exports:

    Repo:
        Session API for opening and mutating a fits repository.

    ObjectTypeName:
        Validated object type name for ``new_node``.

    Id, TargetId:
        Validated canonical and create-time target identifiers.

    Graph, GraphNode, GraphEdge:
        Typed models for ``output_graph`` responses.

    Result, Ok, Err:
        Generic result type for operational libfits failures (from the
        `result <https://pypi.org/project/result/>`_ package).

    ValidateResult, ValidateSummary, ValidationIssue:
        Typed models for ``validate`` responses.

    FitsError, FitsSchemaError, FitsStatus:
        Error payload types for ``Err`` variants.

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
    Graph,
    GraphEdge,
    GraphNode,
    Id,
    ObjectTypeName,
    TargetId,
    ValidateResult,
    ValidateSummary,
    ValidationIssue,
)
from pyfits.repo import Repo
from pyfits.result import Err, Ok, Result, is_err, is_ok

try:
    __version__ = version("pyfits")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"

__all__ = [
    "Err",
    "FitsError",
    "FitsSchemaError",
    "FitsStatus",
    "Graph",
    "GraphEdge",
    "GraphNode",
    "Id",
    "ObjectTypeName",
    "Ok",
    "Repo",
    "Result",
    "TargetId",
    "ValidateResult",
    "ValidateSummary",
    "ValidationIssue",
    "__version__",
    "is_err",
    "is_ok",
    "libfits_version_major",
    "api_version_minor",
    "libfits_version_packed",
    "libfits_version_string",
    "lib_path",
]
