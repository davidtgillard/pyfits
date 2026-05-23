"""Typed models for libfits requests and JSON responses."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Literal

from pyfits._errors import FitsError, FitsSchemaError
from pyfits.result import Err, Ok, Result

_OBJECT_TYPE_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
"""Object type name pattern.

ASCII letter first, then letters, digits, underscores, or hyphens.
"""


@dataclass(frozen=True, slots=True)
class ObjectTypeName:
    """Validated object type name for node allocation.

    Type name strings must be non-empty, start with an ASCII letter, and contain
    only ASCII letters, digits, underscores, and hyphens thereafter.

    Attributes:
        value: Validated type name string sent to libfits as ``id_prefix``.
    """

    value: str

    def __post_init__(self) -> None:
        if not _OBJECT_TYPE_NAME_RE.fullmatch(self.value):
            msg = (
                "object type name must start with a letter and contain only "
                "letters, digits, underscores, and hyphens"
            )
            raise ValueError(msg)

    def __str__(self) -> str:
        return self.value


Severity = Literal["info", "warn", "error"]
"""Validation issue severity level reported by libfits."""


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """A single validation issue reported by ``validate``.

    Attributes:
        severity: Issue severity level.
        code: Machine-readable issue code from libfits.
        message: Human-readable issue description.
        object_id: Optional graph object id associated with the issue.
    """

    severity: Severity
    code: str
    message: str
    object_id: str | None = None


@dataclass(frozen=True, slots=True)
class ValidateSummary:
    """Aggregate validation issue counts.

    Attributes:
        total_validation_issues: Total number of issues across all severities.
        info_count: Number of informational issues.
        warning_count: Number of warning issues.
        error_count: Number of error issues.
    """

    total_validation_issues: int
    info_count: int
    warning_count: int
    error_count: int


@dataclass(frozen=True, slots=True)
class ValidateResult:
    """Result of repository validation.

    Attributes:
        validation_issues: Individual issues reported by libfits.
        summary: Aggregate counts by severity.
        protocol_version: Optional protocol version echoed by libfits.
    """

    validation_issues: tuple[ValidationIssue, ...]
    summary: ValidateSummary
    protocol_version: int | None = None


def _schema_err(message: str, *, operation: str) -> Err[FitsError]:
    return Err(
        FitsSchemaError(
            message,
            operation=operation,
            schema_id="invariant",
        )
    )


def _require_dict(
    value: Any,
    field: str,
    operation: str,
) -> Result[dict[str, Any], FitsError]:
    if not isinstance(value, dict):
        msg = f"{operation} success response missing {field}"
        return _schema_err(msg, operation=operation)
    return Ok(value)


def parse_validate_result(doc: dict[str, Any]) -> Result[ValidateResult, FitsError]:
    """Build a :class:`ValidateResult` from a schema-validated success document.

    Args:
        doc: Parsed ``validate`` success response with ``ok: true``.

    Returns:
        ``Ok(ValidateResult)`` on success, or ``Err(FitsError)`` when invariants
        fail.
    """
    operation = "validate"
    if doc.get("ok") is not True:
        msg = "expected ok=true validate response"
        return _schema_err(msg, operation=operation)

    issues_raw = doc.get("validation_issues")
    if not isinstance(issues_raw, list):
        msg = "validate success response missing validation_issues array"
        return _schema_err(msg, operation=operation)

    summary_raw = doc.get("summary")
    match _require_dict(summary_raw, "summary", operation):
        case Err(error):
            return Err(error)
        case Ok(summary_dict):
            pass

    validation_issues: list[ValidationIssue] = []
    for item in issues_raw:
        if not isinstance(item, dict):
            msg = "validation issue must be an object"
            return _schema_err(msg, operation=operation)
        sev = item.get("severity")
        code = item.get("code")
        message = item.get("message")
        if sev not in ("info", "warn", "error"):
            msg = f"invalid validation issue severity: {sev!r}"
            return _schema_err(msg, operation=operation)
        if not isinstance(code, str) or not isinstance(message, str):
            msg = "validation issue missing code or message"
            return _schema_err(msg, operation=operation)
        oid = item.get("object_id")
        object_id = oid if isinstance(oid, str) else None
        validation_issues.append(
            ValidationIssue(
                severity=sev,
                code=code,
                message=message,
                object_id=object_id,
            )
        )

    def _int_field(name: str) -> Result[int, FitsError]:
        val = summary_dict.get(name)
        if not isinstance(val, int):
            msg = f"summary.{name} must be an integer"
            return _schema_err(msg, operation=operation)
        return Ok(val)

    fields: dict[str, int] = {}
    for name in (
        "total_validation_issues",
        "info_count",
        "warning_count",
        "error_count",
    ):
        match _int_field(name):
            case Err(error):
                return Err(error)
            case Ok(value):
                fields[name] = value

    summary = ValidateSummary(
        total_validation_issues=fields["total_validation_issues"],
        info_count=fields["info_count"],
        warning_count=fields["warning_count"],
        error_count=fields["error_count"],
    )
    proto = doc.get("protocol_version")
    protocol_version = proto if isinstance(proto, int) else None
    return Ok(
        ValidateResult(
            validation_issues=tuple(validation_issues),
            summary=summary,
            protocol_version=protocol_version,
        )
    )


def parse_new_node_id(doc: dict[str, Any]) -> Result[str, FitsError]:
    """Return ``node_id`` from a ``new_node`` success response.

    Args:
        doc: Parsed ``new_node`` success response with ``ok: true``.

    Returns:
        ``Ok(node_id)`` on success, or ``Err(FitsError)`` when ``node_id`` is
        missing or invalid.
    """
    operation = "new_node"
    node_id = doc.get("node_id")
    if not isinstance(node_id, str):
        msg = "new_node success response missing node_id"
        return _schema_err(msg, operation=operation)
    return Ok(node_id)


def parse_output_graph(doc: dict[str, Any]) -> Result[dict[str, Any], FitsError]:
    """Return the graph object from an ``output_graph`` success response.

    Args:
        doc: Parsed ``output_graph`` success response with ``ok: true``.

    Returns:
        ``Ok(graph)`` on success, or ``Err(FitsError)`` when ``graph`` is missing
        or invalid.
    """
    operation = "output_graph"
    graph = doc.get("graph")
    if not isinstance(graph, dict):
        msg = "output_graph success response missing graph object"
        return _schema_err(msg, operation=operation)
    return Ok(graph)
