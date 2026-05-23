"""Typed models for libfits JSON responses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from pyfits._errors import FitsSchemaError

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


def _require_dict(value: Any, field: str, operation: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        msg = f"{operation} success response missing {field}"
        raise FitsSchemaError(
            msg,
            operation=operation,
            schema_id="invariant",
        )
    return value


def parse_validate_result(doc: dict[str, Any]) -> ValidateResult:
    """Build a :class:`ValidateResult` from a schema-validated success document.

    Args:
        doc: Parsed ``validate`` success response with ``ok: true``.

    Returns:
        Structured validation issues and summary counts.

    Raises:
        FitsSchemaError: When required fields are missing or have invalid types.
    """
    operation = "validate"
    if doc.get("ok") is not True:
        msg = "expected ok=true validate response"
        raise FitsSchemaError(msg, operation=operation, schema_id="invariant")

    issues_raw = doc.get("validation_issues")
    if not isinstance(issues_raw, list):
        msg = "validate success response missing validation_issues array"
        raise FitsSchemaError(msg, operation=operation, schema_id="invariant")

    summary_raw = doc.get("summary")
    summary_dict = _require_dict(summary_raw, "summary", operation)

    validation_issues: list[ValidationIssue] = []
    for item in issues_raw:
        if not isinstance(item, dict):
            msg = "validation issue must be an object"
            raise FitsSchemaError(msg, operation=operation, schema_id="invariant")
        sev = item.get("severity")
        code = item.get("code")
        message = item.get("message")
        if sev not in ("info", "warn", "error"):
            msg = f"invalid validation issue severity: {sev!r}"
            raise FitsSchemaError(msg, operation=operation, schema_id="invariant")
        if not isinstance(code, str) or not isinstance(message, str):
            msg = "validation issue missing code or message"
            raise FitsSchemaError(msg, operation=operation, schema_id="invariant")
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

    def _int_field(name: str) -> int:
        val = summary_dict.get(name)
        if not isinstance(val, int):
            msg = f"summary.{name} must be an integer"
            raise FitsSchemaError(msg, operation=operation, schema_id="invariant")
        return val

    summary = ValidateSummary(
        total_validation_issues=_int_field("total_validation_issues"),
        info_count=_int_field("info_count"),
        warning_count=_int_field("warning_count"),
        error_count=_int_field("error_count"),
    )
    proto = doc.get("protocol_version")
    protocol_version = proto if isinstance(proto, int) else None
    return ValidateResult(
        validation_issues=tuple(validation_issues),
        summary=summary,
        protocol_version=protocol_version,
    )


def parse_new_node_id(doc: dict[str, Any]) -> str:
    """Return ``node_id`` from a ``new_node`` success response.

    Args:
        doc: Parsed ``new_node`` success response with ``ok: true``.

    Returns:
        Allocated node identifier string.

    Raises:
        FitsSchemaError: When ``node_id`` is missing or not a string.
    """
    operation = "new_node"
    node_id = doc.get("node_id")
    if not isinstance(node_id, str):
        msg = "new_node success response missing node_id"
        raise FitsSchemaError(msg, operation=operation, schema_id="invariant")
    return node_id


def parse_output_graph(doc: dict[str, Any]) -> dict[str, Any]:
    """Return the graph object from an ``output_graph`` success response.

    Args:
        doc: Parsed ``output_graph`` success response with ``ok: true``.

    Returns:
        Graph object from the libfits response (JSON-serializable mapping).

    Raises:
        FitsSchemaError: When ``graph`` is missing or not an object.
    """
    operation = "output_graph"
    graph = doc.get("graph")
    if not isinstance(graph, dict):
        msg = "output_graph success response missing graph object"
        raise FitsSchemaError(msg, operation=operation, schema_id="invariant")
    return graph
