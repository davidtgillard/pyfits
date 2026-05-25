"""Typed models for libfits requests and JSON responses."""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Literal

from pyrsistent import pvector
from pyrsistent.typing import PVector

from pyfits.errors import FitsError, FitsSchemaError
from pyfits.result import Err, Ok, Result

_OBJECT_TYPE_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
"""Object type name pattern.

ASCII letter first, then letters, digits, underscores, or hyphens.
"""

_AUTONUMBER_SEGMENT_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*-[1-9][0-9]*$")
"""Autonumber-shaped id segment: ``{prefix}-{n}`` with positive ``n``."""

_FORBIDDEN_FS_CHARS = '<>:"|?*\\'
"""NTFS-forbidden characters plus backslash (mirrors libfits instance_name.zig)."""


def _wire_id_from_response(raw: str) -> str:
    """Strip optional title suffix from libfits display ids in create responses."""
    if "/" not in raw:
        return raw.split(" ", 1)[0]
    parts = raw.split("/")
    parts[-1] = parts[-1].split(" ", 1)[0]
    return "/".join(parts)


def _validate_segment(segment: str) -> None:
    if not segment:
        msg = "id segment must be non-empty"
        raise ValueError(msg)
    if _AUTONUMBER_SEGMENT_RE.fullmatch(segment):
        return
    if any(c.isspace() for c in segment):
        msg = "id segment must not contain whitespace"
        raise ValueError(msg)
    if "/" in segment or "\\" in segment:
        msg = "id segment must not contain path separators"
        raise ValueError(msg)
    if any(c in _FORBIDDEN_FS_CHARS for c in segment):
        msg = "id segment contains forbidden characters"
        raise ValueError(msg)
    if segment.endswith(".") or segment.endswith(" "):
        msg = "id segment must not end with '.' or space"
        raise ValueError(msg)
    if "." in segment:
        msg = "id segment must not contain '.'"
        raise ValueError(msg)
    if any(ord(c) < 32 or ord(c) == 127 for c in segment):
        msg = "id segment must not contain ASCII control characters"
        raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class ObjectTypeName:
    """Validated object type name for node creation.

    Type name strings must be non-empty, start with an ASCII letter, and contain
    only ASCII letters, digits, underscores, and hyphens thereafter.

    Attributes:
        value: Validated type name string sent to libfits as ``type_name``.
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


@dataclass(frozen=True, slots=True)
class TargetId:
    """Single-segment id requested at create time (never returned from libfits).

    Attributes:
        value: Validated single-segment id serialized to wire ``target_id``.
    """

    value: str

    def __post_init__(self) -> None:
        if "/" in self.value:
            msg = "TargetId must be a single segment"
            raise ValueError(msg)
        _validate_segment(self.value)

    @classmethod
    def parse(cls, raw: str) -> TargetId:
        """Parse and validate ``raw`` as a :class:`TargetId`.

        Args:
            raw: Single-segment id string.

        Returns:
            Validated target id.

        Raises:
            ValueError: When ``raw`` is not a valid target id.
        """
        return cls(raw)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class Id:
    """Canonical validated graph object identifier (libfits wire/API form).

    Attributes:
        value: Repo-logical id string (one or more ``/``-separated segments).
    """

    value: str
    _segments: PVector[str] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not self.value:
            msg = "Id must be non-empty"
            raise ValueError(msg)
        segments = self.value.split("/")
        if any(not segment for segment in segments):
            msg = "Id must not contain empty path segments"
            raise ValueError(msg)
        for segment in segments:
            _validate_segment(segment)
        object.__setattr__(self, "_segments", pvector(segments))

    @classmethod
    def parse(cls, raw: str) -> Id:
        """Parse and validate ``raw`` as an :class:`Id`.

        Args:
            raw: Canonical id string.

        Returns:
            Validated id.

        Raises:
            ValueError: When ``raw`` is not a valid id.
        """
        return cls(raw)

    @classmethod
    def try_parse(cls, raw: str) -> Id | None:
        """Return an :class:`Id` for ``raw``, or ``None`` when invalid.

        Args:
            raw: Candidate id string.

        Returns:
            Parsed id, or ``None`` when validation fails.
        """
        try:
            return cls(raw)
        except ValueError:
            return None

    @property
    def segments(self) -> Sequence[str]:
        """Return path segments of this id."""
        return self._segments

    @classmethod
    def join(cls, parent: Id, target: TargetId) -> Id:
        """Join a parent id and create-time target segment.

        Args:
            parent: Parent canonical id.
            target: Single-segment target id.

        Returns:
            Combined canonical id.
        """
        if not parent.value:
            return cls(target.value)
        return cls(f"{parent.value}/{target.value}")

    def __str__(self) -> str:
        return self.value


Severity = Literal["info", "warn", "error"]
"""Validation issue severity level reported by libfits."""

EdgeKind = Literal["references", "registered_link"]
"""Edge relationship kind in serialized graph output."""


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
    object_id: Id | None = None


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

    validation_issues: Sequence[ValidationIssue]
    summary: ValidateSummary
    protocol_version: int | None = None


@dataclass(frozen=True, slots=True)
class GraphNode:
    """One node in a serialized repository graph.

    Attributes:
        id: Canonical node id.
        parent_id: Parent id when nested nodes are included in graph output.
    """

    id: Id
    parent_id: Id | None = None


@dataclass(frozen=True, slots=True)
class GraphEdge:
    """One edge in a serialized repository graph.

    Attributes:
        from_id: Source node id.
        to_id: Target node id.
        kind: Relationship semantics.
        link_type: Registered link type name when ``kind`` is ``registered_link``.
        id: Canonical link id for nested edges when present.
        parent_id: Parent id for nested edges when present.
    """

    from_id: Id
    to_id: Id
    kind: EdgeKind
    link_type: str
    id: Id | None = None
    parent_id: Id | None = None


@dataclass(frozen=True, slots=True)
class Graph:
    """Serialized repository graph snapshot.

    Attributes:
        nodes: Graph node vertices.
        edges: Directed graph edges.
    """

    nodes: Sequence[GraphNode]
    edges: Sequence[GraphEdge]


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


def _parse_id_field(
    raw: Any,
    *,
    operation: str,
    field: str,
    required: bool = True,
) -> Result[Id | None, FitsError]:
    if raw is None:
        if required:
            msg = f"{operation} success response missing {field}"
            return _schema_err(msg, operation=operation)
        return Ok(None)
    if not isinstance(raw, str):
        msg = f"{operation} success response {field} must be a string"
        return _schema_err(msg, operation=operation)
    parsed = Id.try_parse(raw)
    if parsed is None:
        msg = f"{operation} success response has invalid {field}: {raw!r}"
        return _schema_err(msg, operation=operation)
    return Ok(parsed)


def _parse_required_id(
    raw: Any,
    *,
    operation: str,
    field: str,
) -> Result[Id, FitsError]:
    parsed = _parse_id_field(raw, operation=operation, field=field, required=True)
    if isinstance(parsed, Err):
        return parsed
    if parsed.ok_value is None:
        msg = f"{operation} success response missing {field}"
        return _schema_err(msg, operation=operation)
    return Ok(parsed.ok_value)


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
    summary_result = _require_dict(summary_raw, "summary", operation)
    if isinstance(summary_result, Err):
        return summary_result
    summary_dict = summary_result.ok_value

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
        object_id: Id | None = None
        if isinstance(oid, str):
            object_id = Id.try_parse(oid)
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
        int_result = _int_field(name)
        if isinstance(int_result, Err):
            return int_result
        fields[name] = int_result.ok_value

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
            validation_issues=pvector(validation_issues),
            summary=summary,
            protocol_version=protocol_version,
        )
    )


def parse_new_node_id(doc: dict[str, Any]) -> Result[Id, FitsError]:
    """Return ``node_id`` from a ``new_node`` success response.

    Args:
        doc: Parsed ``new_node`` success response with ``ok: true``.

    Returns:
        ``Ok(Id)`` on success, or ``Err(FitsError)`` when ``node_id`` is missing
        or invalid.
    """
    raw = doc.get("node_id")
    if not isinstance(raw, str):
        return _parse_required_id(
            raw,
            operation="new_node",
            field="node_id",
        )
    return _parse_required_id(
        _wire_id_from_response(raw),
        operation="new_node",
        field="node_id",
    )


def parse_new_link_id(doc: dict[str, Any]) -> Result[Id, FitsError]:
    """Return ``link_id`` from a ``new_link`` success response.

    Args:
        doc: Parsed ``new_link`` success response with ``ok: true``.

    Returns:
        ``Ok(Id)`` on success, or ``Err(FitsError)`` when ``link_id`` is missing
        or invalid.
    """
    return _parse_required_id(
        doc.get("link_id"),
        operation="new_link",
        field="link_id",
    )


def parse_rename_instance_id(doc: dict[str, Any]) -> Result[Id, FitsError]:
    """Return ``target_id`` from a ``rename_instance`` success response.

    Args:
        doc: Parsed ``rename_instance`` success response with ``ok: true``.

    Returns:
        ``Ok(Id)`` on success, or ``Err(FitsError)`` when ``target_id`` is
        missing or invalid.
    """
    return _parse_required_id(
        doc.get("target_id"),
        operation="rename_instance",
        field="target_id",
    )


def parse_output_graph(doc: dict[str, Any]) -> Result[Graph, FitsError]:
    """Return a typed graph from an ``output_graph`` success response.

    Args:
        doc: Parsed ``output_graph`` success response with ``ok: true``.

    Returns:
        ``Ok(Graph)`` on success, or ``Err(FitsError)`` when the graph shape is
        missing or invalid.
    """
    operation = "output_graph"
    graph = doc.get("graph")
    if not isinstance(graph, dict):
        msg = "output_graph success response missing graph object"
        return _schema_err(msg, operation=operation)

    nodes_raw = graph.get("nodes")
    edges_raw = graph.get("edges")
    if not isinstance(nodes_raw, list):
        msg = "output_graph graph missing nodes array"
        return _schema_err(msg, operation=operation)
    if not isinstance(edges_raw, list):
        msg = "output_graph graph missing edges array"
        return _schema_err(msg, operation=operation)

    nodes: list[GraphNode] = []
    for item in nodes_raw:
        if not isinstance(item, dict):
            msg = "graph node must be an object"
            return _schema_err(msg, operation=operation)
        node_id_result = _parse_required_id(
            item.get("id"),
            operation=operation,
            field="node.id",
        )
        if isinstance(node_id_result, Err):
            return node_id_result
        node_id = node_id_result.ok_value
        node_parent_id: Id | None = None
        if "parent_id" in item:
            parent_result = _parse_id_field(
                item.get("parent_id"),
                operation=operation,
                field="node.parent_id",
            )
            if isinstance(parent_result, Err):
                return parent_result
            node_parent_id = parent_result.ok_value
        nodes.append(GraphNode(id=node_id, parent_id=node_parent_id))

    edges: list[GraphEdge] = []
    for item in edges_raw:
        if not isinstance(item, dict):
            msg = "graph edge must be an object"
            return _schema_err(msg, operation=operation)
        kind = item.get("kind")
        link_type = item.get("link_type")
        if kind not in ("references", "registered_link"):
            msg = f"invalid graph edge kind: {kind!r}"
            return _schema_err(msg, operation=operation)
        if not isinstance(link_type, str):
            msg = "graph edge missing link_type"
            return _schema_err(msg, operation=operation)
        from_id_result = _parse_required_id(
            item.get("from_id"),
            operation=operation,
            field="edge.from_id",
        )
        if isinstance(from_id_result, Err):
            return from_id_result
        from_id = from_id_result.ok_value
        to_id_result = _parse_required_id(
            item.get("to_id"),
            operation=operation,
            field="edge.to_id",
        )
        if isinstance(to_id_result, Err):
            return to_id_result
        to_id = to_id_result.ok_value
        edge_id: Id | None = None
        if "id" in item:
            edge_id_result = _parse_id_field(
                item.get("id"),
                operation=operation,
                field="edge.id",
                required=False,
            )
            if isinstance(edge_id_result, Err):
                return edge_id_result
            edge_id = edge_id_result.ok_value
        edge_parent_id: Id | None = None
        if "parent_id" in item:
            edge_parent_result = _parse_id_field(
                item.get("parent_id"),
                operation=operation,
                field="edge.parent_id",
                required=False,
            )
            if isinstance(edge_parent_result, Err):
                return edge_parent_result
            edge_parent_id = edge_parent_result.ok_value
        edges.append(
            GraphEdge(
                from_id=from_id,
                to_id=to_id,
                kind=kind,
                link_type=link_type,
                id=edge_id,
                parent_id=edge_parent_id,
            )
        )

    return Ok(Graph(nodes=pvector(nodes), edges=pvector(edges)))


def format_output_graph_json(
    doc: dict[str, Any],
    *,
    pretty_print: bool = False,
) -> Result[str, FitsError]:
    """Return the graph object from an ``output_graph`` response as JSON text.

    Args:
        doc: Parsed ``output_graph`` success response with ``ok: true``.
        pretty_print: When ``True``, indent the JSON for human-readable output.

    Returns:
        ``Ok(json_text)`` on success, or ``Err(FitsError)`` when the graph
        object is missing or not JSON-serializable.
    """
    operation = "output_graph"
    graph = doc.get("graph")
    if not isinstance(graph, dict):
        msg = "output_graph success response missing graph object"
        return _schema_err(msg, operation=operation)
    try:
        if pretty_print:
            text = json.dumps(graph, indent=2, ensure_ascii=False) + "\n"
        else:
            text = json.dumps(graph, separators=(",", ":"), ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        msg = f"output_graph graph is not JSON-serializable: {exc}"
        return Err(FitsError(msg, code="invalid_json"))
    return Ok(text)
