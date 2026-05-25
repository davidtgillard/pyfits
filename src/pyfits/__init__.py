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

    Version, get_version:
        Loaded libfits C ABI and package version information.
"""

from importlib.metadata import PackageNotFoundError, version

from pyfits._version_abi import Version, get_version
from pyfits.errors import FitsError, FitsSchemaError, FitsStatus
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
    "Version",
    "__version__",
    "get_version",
    "is_err",
    "is_ok",
]
